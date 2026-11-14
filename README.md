# 단테 2D 캐릭터 실습

제공된 강의의 구조를 현재 캐릭터 리소스와 조작에 맞게 적용했습니다.
실제 캐릭터 구현 파일은 `character.py`입니다. 기존 루트의 `test_character.py`는
검증 코드이므로 `tests/test_controller.py`로 이동했습니다.

## 실행

프로젝트 폴더 `C:\2D_Game_Project`에서 실행합니다.

```powershell
python -m pip install -r requirements.txt
python main.py
```

**Devil May Cry:생존3분** 시작 화면에서 Enter를 누르면 플레이가 시작됩니다.
우측 상단의 생존 타이머는 3:00부터 0:00까지 남은 시간을 표시합니다.
Esc를 누르거나 창을 닫으면 게임을 종료합니다.

이미지는 `load_image('character1.png')`처럼 파일명으로 직접 읽습니다.
`pathlib.Path`를 사용하지 않습니다.

| 키 | 동작 |
| --- | --- |
| 방향키 또는 A/D | 이동 |
| U | 기본 검 공격 |
| J | 점프, 공중 좌우 이동 |
| P | 1스테이지에서 깊은 정글로 이동합니다. 2스테이지의 생존 타이머는 3:00부터 시작합니다. |
| I | 돌진 찌르기 |
| O | 올려베기 |
| L | 데빌 트리거. 변신 순간 반경 300픽셀의 붉은 충격파가 퍼지며 닿은 적마다 피해 40을 한 번 줍니다. 변신 후 악마 상태는 30초, 재사용은 발동 후 1초입니다. 좌측 상단 보라색 게이지가 남은 변신 시간을 표시합니다. |
| K | 지상에서는 짧은 도약 후 내려찍기, 공중에서는 즉시 내려찍기. 착지 타격이나 좌우로 퍼지는 붉은 파동에 닿은 적은 K 한 번당 피해 38을 한 번 받습니다. 낙하 거리가 길수록 파동이 더 크고 멀리 뻗으며, 520픽셀 낙하 시 기본 크기의 2배에 도달합니다. |
| ESC 또는 창 닫기 | 종료 |

## 강의 내용과 코드 연결

| 강의 | 적용한 내용 | 구현 위치 |
| --- | --- | --- |
| LEC 08 애니메이션, 5~16번 슬라이드 | action/프레임, 프레임 순환, 영역 자르기, 수평 반전 | `character.py`: ANIMATIONS, PIVOTS, draw |
| LEC 09 애니메이션 뷰어 제작 실습, 7번 슬라이드 | 경과 시간에 따른 이동과 프레임 전환 | `main.py`, `Character.update` |
| LEC 10 입력 처리, 6~13번 슬라이드 | KEYDOWN/KEYUP, dir, 입력·갱신·출력 분리 | `Character.handle_event`, `read_direction`, `play_mode.py` |
| LEC 11 게임 오브젝트, 19~24쪽 | 배경과 캐릭터의 클래스, update/draw | `background.py`, `character.py` |
| LEC 12 캐릭터 컨트롤러(1), 6·9·24~26쪽 | 클래스 변수로 이미지 공유, transitions.Machine | `Character.images`, `Character.machine` |
| LEC 13 캐릭터 컨트롤러(2), 6쪽 | 하나의 RUN 상태, 이동 방향, 화면 경계 | `TRANSITIONS`, `face_dir`, `_move_x` |
| LEC 14 게임 월드, 12~14쪽 | 리스트를 이용한 배경/전경 레이어 | `game_world.py` |
| LEC 15 게임 프레임웍, 5~6쪽 | main과 play_mode 분리, init/update/draw/finish | `main.py`, `play_mode.py` |

15강의 단계별 구조 중 플레이 모드 분리 단계까지 적용했습니다.
타이틀 모드(`title_mode.py`)는 `Game_Start.png`를 표시하고 Enter 입력을 받으면 플레이 모드로 전환합니다.
점프 중력, 도약·내려찍기, 돌진, 발 기준점 보정은 기존 게임의 동작을 유지하기 위한 확장입니다.
`update(delta_time)`는 9강의 경과 시간 처리를 각 오브젝트에 전달하도록 적용한 형태입니다.

## 상태 전이

`transitions.Machine`의 `auto_transitions=False`로 전이 표에 선언한 이벤트만 사용합니다.
상태를 바꿀 때 `reset_animation`이 프레임과 재생 시간을 초기화합니다.

| 출발 상태 | 이벤트 | 도착 상태 |
| --- | --- | --- |
| IDLE | 이동 방향 입력 | RUN |
| RUN | 이동 방향이 0 | IDLE |
| IDLE / RUN | U / J / I / O / K | ATTACK / JUMP / THRUST / UPPERCUT / SLAM |
| JUMP, 공중일 때 | K | SLAM |
| 공격 또는 점프 상태 | 동작 완료, 이동 키 누름 | RUN |
| 공격 또는 점프 상태 | 동작 완료, 이동 키 없음 | IDLE |

공격 중 다른 공격이나 점프로 다시 시작하지 않습니다.
점프의 도약 준비·상승·공중·착지와 내려찍기의 충격 프레임은 실제 높이에 맞춰 처리합니다.
`character1.png`는 대기·이동·기본 공격, `character2.png`는 점프·추가 스킬에 사용합니다.
1단계에는 다섯 종류의 적이 한 마리씩 등장합니다. 잿불 정령은 화염탄을 쏘고, 사슬 사냥개는 수평으로 돌진합니다. 성당 가고일은 조준선을 따라 급강하하고, 종탑 처형자는 바닥을 강타합니다. 성가대 망령은 보라색 원 안을 공격한 뒤 순간이동합니다.
종탑 처형자는 0.85초 동안 두 주먹을 들어 경고한 뒤 0.16초 동안 내려찍습니다. 주먹이 지면에 닿을 때 피해가 한 번 발생하고, 바닥의 충격선과 파편이 표시됩니다. 좌우 165픽셀 밖으로 이동하거나 발이 지면에서 72픽셀 이상 높아지도록 점프하면 피할 수 있습니다.

U·I·O의 검격, K의 착지 타격, L의 변신 충격파로 적을 처치할 수 있습니다. 단테가 적에게 맞으면 HP가 줄고 0.65초간 추가 피해를 피합니다.

## 검증

```powershell
python -m unittest discover -s tests -v
```

상태 전이, 연속 입력, 착지, 공중 내려찍기, 이미지 공유, 레이어 순서, 종료 처리를 검증합니다.
설치된 pico2d 1.5.0의 `get_events()`가 SDL_QUIT를 목록에 넣지 않는 부분은
`play_mode.handle_events`에서 SDL 종료 이벤트를 먼저 확인해 보완했습니다.
