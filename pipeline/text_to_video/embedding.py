import faiss
import json
import os
import numpy as np
import requests
from sentence_transformers import SentenceTransformer


class FaissSearch:
    """FAISS 기반 검색 시스템 클래스"""

    def __init__(self, json_path, model_name="all-MiniLM-L6-v2", use_gpu=True):
        self.json_path = json_path
        self.model = SentenceTransformer(model_name)

        # JSON 데이터 로드 또는 생성
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                
            # 임베딩이 없는 경우 생성
            if "embedding" not in self.data[0]:
                print("📂 임베딩 벡터 생성 중...")
                for entry in self.data:
                    entry["embedding"] = self.model.encode(entry["caption"]).tolist()
                
                # 임베딩이 추가된 JSON 저장
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=4, ensure_ascii=False)
                print(f"✅ 임베딩 벡터 저장 완료 → {self.json_path}")
        else:
            print(f"🚨 오류: {self.json_path} 파일을 찾을 수 없습니다!")
            return

        # 임베딩 배열 생성
        self.captions = [entry["caption"] for entry in self.data]
        self.embeddings = np.array([entry["embedding"] for entry in self.data], dtype=np.float32)
        faiss.normalize_L2(self.embeddings)

        # FAISS 인덱스 초기화
        self._initialize_faiss(use_gpu)

    def _load_json_data(self):
        """JSON 파일을 로드하여 캡션 및 임베딩을 가져옴"""
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.captions = [entry["caption"] for entry in self.data]
        self.embeddings = np.array([entry["embedding"] for entry in self.data], dtype=np.float32)
        faiss.normalize_L2(self.embeddings)

    def _initialize_faiss(self, use_gpu):
        """FAISS 인덱스를 생성 및 초기화"""
        self.dimension = self.embeddings.shape[1]
        self.res = faiss.StandardGpuResources() if use_gpu else None
        self.index = faiss.IndexFlatIP(self.dimension)
        self.gpu_index = faiss.index_cpu_to_gpu(self.res, 0, self.index) if use_gpu else self.index
        self.gpu_index.add(self.embeddings)

    def find_similar_captions(self, input_text, translator, top_k=3):
        """한국어 입력 → 영어 변환 → FAISS 검색 → 한국어 변환 후 결과 반환"""
        translated_query = translator.translate_ko_to_en(input_text)
        if not translated_query:
            print("🚨 번역 실패! 입력 텍스트를 확인하세요.")
            return []

        query_embedding = self.model.encode([translated_query]).astype(np.float32)
        faiss.normalize_L2(query_embedding)

        D, I = self.gpu_index.search(query_embedding, top_k)
        
        results = []
        for idx, i in enumerate(I[0]):
            caption_ko = translator.translate_en_to_ko(self.captions[i])
            video_info = {
                'video_path': self.data[i]['video_path'],
                'video_id': self.data[i]['video_id'],
                'clip_id': self.data[i]['clip_id'],
                'start_time': self.data[i]['start_time'],
                'end_time': self.data[i]['end_time']
            }
            results.append((caption_ko, D[0][idx], video_info))

        return results

    def compute_similarity(self, query, caption, translator):
        """쿼리와 캡션 간의 유사도 계산"""
        # 쿼리를 영어로 번역
        query_en = translator.translate_ko_to_en(query)
        
        # 텍스트를 임베딩 벡터로 변환
        query_embedding = self.model.encode([query_en])[0]
        caption_embedding = self.model.encode([caption])[0]
        
        # FAISS와 동일한 방식으로 유사도 계산
        l2_distance = np.linalg.norm(query_embedding - caption_embedding)
        similarity = 1 - l2_distance/2
        
        return max(0, min(1, similarity))  # 0~1 범위로 클리핑
