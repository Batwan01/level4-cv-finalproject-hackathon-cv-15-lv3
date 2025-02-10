<p align='center'>
    <img src="https://capsule-render.vercel.app/api?type=waving&color=auto&height=300&section=header&text=Tving-Hackathon&fontSize=40&animation=fadeIn&fontAlignY=38&desc=CV-15&descAlignY=51&descAlign=62"/>
</p>

# Video to Text (Captioning)
<img width="726" alt="스크린샷 2025-02-10 오후 5 38 53" src="https://github.com/user-attachments/assets/5e2f4442-326f-459e-9611-0bac2533db7c" />

# Text to Video (Retrieval)
<img width="749" alt="스크린샷 2025-02-10 오후 5 39 38" src="https://github.com/user-attachments/assets/e879bc4b-456e-43d0-96fe-7ff86ec0770d" />

# Full Pipeline 
<img width="773" alt="스크린샷 2025-02-10 오후 5 43 58" src="https://github.com/user-attachments/assets/44d2f2aa-d935-4cd1-8205-472953a533ca" />


### Filter의 ID(mid)값 찾기 
```
cd dataset
grep "{Filter Name}" id.txt
```


***Example Usage***
```
grep "Movie theater" id.txt
```

<br>

### ID에 해당하는 list만들기
```
curl -o id_list/{file name}.txt https://storage.googleapis.com/data.yt8m.org/2/j/v/{id}.js
```

***Example Usage***
```
curl -o id_list/movie_ids.txt https://storage.googleapis.com/data.yt8m.org/2/j/v/0kcc7.js
```
<br>

### Filter의 데이터 다운로드
```
partition=2/frame/train mirror=asia python download_and_process.py
```

<br>

# My Project
This project focuses on using the YouTube 8M dataset to develop models for video-to-text and text-to-video applications.

The primary goal is to enable efficient translation of video content into meaningful textual descriptions and to identify matching video scenes based on text input.

## Features
- **Video-to-Text**: Generate detailed captions or descriptions from video data.
- **Text-to-Video**: Identify and retrieve video scenes that match the given text input.

## Dataset
This project leverages the [YouTube 8M dataset](https://research.google.com/youtube8m/) for training and evaluation.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

License를 써야 할지 모르겠어서 아직 추가 안헀습니다.
