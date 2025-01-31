import pandas as pd
import json
import numpy as np
import os
from text_to_video.embedding import FaissSearch
from utils.translator import DeepGoogleTranslator

def get_video_clips(db_data, video_identifier, db_type):
    """DB 타입에 따라 다른 방식으로 비디오 클립 추출"""
    video_clips = []
    
    if db_type == "clips":  # clips_embedding.json 형식
        for clip in db_data:
            if clip['video_id'] == video_identifier:  # video_id로 매칭
                video_clips.append(clip)
    else:  # t2v_captions.json 형식
        for clip in db_data:
            if video_identifier in clip['video_path']:  # video_path로 매칭
                video_clips.append(clip)
    
    return video_clips

def compute_metrics(timestamps, similarities, gt_start, gt_end, threshold=0.5):
    """주어진 유사도 그래프에 대한 평가 지표 계산"""
    metrics = {
        'max_similarity': 0,  # 정답 구간 내 최대 유사도
        'mean_similarity': 0,  # 정답 구간 내 평균 유사도
        'gt_coverage': 0,     # 정답 구간 내 높은 유사도(임계값 이상) 비율
        'precision': 0,       # 검출된 구간 중 정답 구간과 겹치는 비율
        'recall': 0,          # 정답 구간 중 검출된 비율
        'f1_score': 0         # F1 점수
    }
    
    # 정답 구간 내 유사도 통계
    gt_similarities = []
    for t, s in zip(timestamps, similarities):
        if gt_start <= t <= gt_end:
            gt_similarities.append(s)
    
    if gt_similarities:
        metrics['max_similarity'] = max(gt_similarities)
        metrics['mean_similarity'] = sum(gt_similarities) / len(gt_similarities)
        
        # 임계값 이상인 비율 계산
        high_similarity_count = sum(1 for s in gt_similarities if s >= threshold)
        metrics['gt_coverage'] = high_similarity_count / len(gt_similarities)
    
    # Precision & Recall 계산을 위한 구간 검출
    detected_segments = []
    current_segment = None
    
    for t, s in zip(timestamps, similarities):
        if s >= threshold:
            if current_segment is None:
                current_segment = [t, t]
            current_segment[1] = t
        elif current_segment is not None:
            detected_segments.append(current_segment)
            current_segment = None
    
    if current_segment is not None:
        detected_segments.append(current_segment)
    
    # IoU 기반 Precision & Recall
    total_intersection = 0
    total_union = 0
    
    for seg in detected_segments:
        intersection_start = max(seg[0], gt_start)
        intersection_end = min(seg[1], gt_end)
        
        if intersection_end > intersection_start:
            intersection = intersection_end - intersection_start
            union = max(seg[1], gt_end) - min(seg[0], gt_start)
            
            total_intersection += intersection
            total_union += union
    
    if total_union > 0:
        metrics['precision'] = total_intersection / total_union
        metrics['recall'] = total_intersection / (gt_end - gt_start)
        
        if metrics['precision'] + metrics['recall'] > 0:
            metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
    
    return metrics

def compare_db_performance(excel_path, db_configs):
    """
    여러 DB의 성능 비교
    
    Args:
        excel_path: 평가 데이터셋 엑셀 파일 경로
        db_configs: [(db_path, db_type), ...] 형식의 설정 리스트
    """
    results = {db_path: {
        'max_similarity': [],
        'mean_similarity': [],
        'gt_coverage': [],
        'precision': [],
        'recall': [],
        'f1_score': []
    } for db_path, _ in db_configs}
    
    for db_path, db_type in db_configs:
        print(f"\n📊 Processing DB: {db_path}")
        df = pd.read_excel(excel_path)
        
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        
        translator = DeepGoogleTranslator()
        faiss_search = FaissSearch(json_path=db_path)
        
        for _, row in df.iterrows():
            # DB 타입에 따라 다른 식별자 사용
            video_identifier = (row['VideoURL'].split('=')[-1] 
                              if db_type == "clips" 
                              else row['MatchedName'])
            
            query = row['Query']
            gt_start = row['StartTime']
            gt_end = row['EndTime']
            
            video_clips = get_video_clips(db_data, video_identifier, db_type)
            
            if not video_clips:
                print(f"⚠️ No clips found for video: {video_identifier}")
                continue
                
            # 시간순 정렬
            video_clips.sort(key=lambda x: float(x['start_time']))
            
            timestamps = []
            similarities = []
            
            for clip in video_clips:
                similarity = faiss_search.compute_similarity(query, clip['caption'], translator)
                timestamps.append(float(clip['start_time']))
                similarities.append(similarity)
            
            if timestamps:
                metrics = compute_metrics(timestamps, similarities, gt_start, gt_end)
                for metric_name in metrics:
                    results[db_path][metric_name].append(metrics[metric_name])
                print(f"✅ Processed video: {video_identifier}")
    
    # 결과 요약
    summary = {}
    for db_path, _ in db_configs:
        db_name = db_path.split('/')[-1].split('.')[0]
        summary[db_name] = {}
        for metric_name in results[db_path]:
            values = results[db_path][metric_name]
            if values:
                summary[db_name][metric_name] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
    
    return summary

def main():
    excel_path = "evaluation_dataset_jhuni_test.xlsx"
    db_configs = [
        ("output/text2video/test_db_d5_t2v_captions.json", "t2v"),
        ("output/text2video/test_db_d1_t2v_captions.json", "t2v"),
        ("output/text2video/clips_embedding.json", "clips")
    ]
    
    summary = compare_db_performance(excel_path, db_configs)
    
    # 결과 출력
    print("\n📊 Performance Summary:")
    for db_name, metrics in summary.items():
        print(f"\n=== {db_name} ===")
        for metric_name, stats in metrics.items():
            print(f"\n{metric_name}:")
            for stat_name, value in stats.items():
                print(f"  {stat_name}: {value:.4f}")

if __name__ == "__main__":
    main()