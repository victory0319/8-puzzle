import streamlit as st
import random
import time
import heapq

# --- 1. 페이지 기본 설정 및 스타일 ---
st.set_page_config(page_title="8-퍼즐 탐색 비교기", layout="wide")

# UI 커스텀 디자인 및 CSS 주입
st.markdown("""
<style>
    .tile {
        background-color: #f4f4f4;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem; font-weight: 500; color: #1a1a1a;
        aspect-ratio: 1; height: 80px; width: 80px; margin: 4px;
    }
    .tile-empty { background-color: #fff; border-color: #eee; color: transparent; }
    .tile-solved { background-color: #e8faf0; border-color: #6dd6a0; }
    .tile-failed { background-color: #fff3f0; border-color: #ffb3a0; }
    
    .goal-tile {
        background-color: #e8faf0; border-radius: 2px;
        display: inline-block; width: 20px; height: 20px;
        text-align: center; font-size: 0.7rem; color: #3aba7a; font-weight: 500;
        margin: 1px; border: 1px solid #6dd6a0;
    }
</style>
""", unsafe_allow_html=True)

GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]

# --- 2. 세션 상태(Session State) 초기화 ---
if 'current_state' not in st.session_state:
    st.session_state.current_state = [1, 2, 3, 4, 0, 5, 7, 8, 6]
if 'stats' not in st.session_state:
    st.session_state.stats = {"nodes": "—", "moves": "—", "time": "—", "status": "알고리즘을 선택하고 탐색을 시작하세요."}

# --- 3. 8-퍼즐 탐색 알고리즘 및 유틸리티 함수 ---
def get_neighbors(state):
    idx = state.index(0)
    row, col = idx // 3, idx % 3
    neighbors = []
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in moves:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            ns = list(state)
            ni = nr * 3 + nc
            ns[idx], ns[ni] = ns[ni], ns[idx]
            neighbors.append(ns)
    return neighbors

def is_solvable(state):
    t = [x for x in state if x != 0]
    inv = 0
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            if t[i] > t[j]:
                inv += 1
    return inv % 2 == 0

def manhattan(state):
    d = 0
    for i in range(9):
        if state[i] == 0:
            continue
        g = GOAL.index(state[i])
        d += abs(i // 3 - g // 3) + abs(i % 3 - g % 3)
    return d

# 알고리즘 함수 내부 튜닝 (기존 로직 유지)
def algo_dfs(start):
    stack = [(start, [start])]
    visited = set()
    nodes = 0
    while stack:
        s, path = stack.pop()
        nodes += 1
        if s == GOAL:
            return path, nodes, False
        if len(path) > 30:
            continue
        k = tuple(s)
        if k in visited:
            continue
        visited.add(k)
        for nb in reversed(get_neighbors(s)):
            if tuple(nb) not in visited:
                stack.append((nb, path + [nb]))
    return None, nodes, True

def algo_bfs(start):
    from collections import deque
    q = deque([(start, [start])])
    visited = {tuple(start)}
    nodes = 0
    while q:
        s, path = q.popleft()
        nodes += 1
        if s == GOAL:
            return path, nodes, False
        for nb in get_neighbors(s):
            k = tuple(nb)
            if k not in visited:
                visited.add(k)
                q.append((nb, path + [nb]))
    return None, nodes, True

def algo_hc(start):
    s = start
    path = [s]
    visited = {tuple(s)}
    nodes = 0
    while True:
        nodes += 1
        if s == GOAL:
            return path, nodes, False
        neighbors = get_neighbors(s)
        best = min(neighbors, key=manhattan)
        if manhattan(best) >= manhattan(s) or tuple(best) in visited:
            return path, nodes, True
        visited.add(tuple(best))
        path.append(best)
        s = best

def algo_bf(start):
    nodes = 0
    heap = [(manhattan(start), nodes, start, [start])]
    visited = set()
    while heap:
        _, _, s, path = heapq.heappop(heap)
        nodes += 1
        if s == GOAL:
            return path, nodes, False
        k = tuple(s)
        if k in visited:
            continue
        visited.add(k)
        for nb in get_neighbors(s):
            if tuple(nb) not in visited:
                heapq.heappush(heap, (manhattan(nb), nodes, nb, path + [nb]))
    return None, nodes, True

# --- 4. 퍼즐판 그리기를 위한 컴포넌트 함수 ---
def draw_puzzle(state, is_solved=False, is_failed=False):
    cols = st.columns(3)
    for i in range(9):
        val = state[i]
        tile_class = "tile"
        if val == 0:
            tile_class += " tile-empty"
        elif is_solved:
            tile_class += " tile-solved"
        elif is_failed:
            tile_class += " tile-failed"
            
        with cols[i % 3]:
            # 코드 하단부 unsafe_allow_box_allowed 매개변수 에러 방지를 위해 제거 후 기본 렌더링
            st.markdown(f'<div class="tile">{val if val != 0 else ""}</div>', unsafe_allow_html=True)

# --- 5. 레이아웃 배치 ---
st.title("8-퍼즐 탐색 비교기 (Streamlit 버전)")
st.caption("DFS · BFS · 언덕 등반 · 최고 우선")

layout_left, layout_right = st.columns([1, 1.2])

# --- 왼쪽: 시각화 및 퍼즐판 제어 ---
with layout_left:
    st.subheader("현재 상태")
    
    # 실시간 렌더링을 위해 비워두는 메인 공간들
    puzzle_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # 맨 처음 로드되었을 때의 퍼즐 상태 시각화
    with puzzle_placeholder.container():
        draw_puzzle(st.session_state.current_state, is_solved=(st.session_state.current_state == GOAL))
    status_placeholder.write(st.session_state.stats["status"])
    
    st.divider()
    st.subheader("초기 상태 설정")
    c1, c2 = st.columns(2)
    
    if c1.button("🎲 랜덤 섞기", use_container_width=True):
        while True:
            arr = [0, 1, 2, 3, 4, 5, 6, 7, 8]
            random.shuffle(arr)
            if is_solvable(arr) and arr != GOAL:
                st.session_state.current_state = arr
                st.session_state.stats = {"nodes": "—", "moves": "—", "time": "—", "status": "새 퍼즐이 설정되었습니다."}
                st.rerun()
                
    if c2.button("↩️ 초기화", use_container_width=True):
        st.session_state.current_state = [1, 2, 3, 4, 0, 5, 7, 8, 6]
        st.session_state.stats = {"nodes": "—", "moves": "—", "time": "—", "status": "초기 상태로 리셋되었습니다."}
        st.rerun()

    speed_ms = st.slider("⏱️ 재생 단계별 대기 속도 (ms)", min_value=100, max_value=800, value=400, step=50)
    speed_sec = speed_ms / 1000.0

# --- 오른쪽: 알고리즘 설정 및 결과 통계 판 ---
with layout_right:
    st.subheader("알고리즘 선택")
    algo_choice = st.radio(
        "탐색 방식을 선택하세요:",
        ["DFS — 깊이 우선 (무정보)", "BFS — 너비 우선 (무정보)", "언덕 등반 탐색 (휴리스틱)", "최고 우선 탐색 (휴리스틱)"],
        label_visibility="collapsed"
    )
    
    desc_box = st.info("")
    algo_key = ""
    if "DFS" in algo_choice:
        desc_box.info("스택으로 최대 깊이까지 탐색 후 되돌아옵니다. 최적 경로를 보장하지 않으며, 깊이 제한(30)을 적용합니다.")
        algo_key = "dfs"
    elif "BFS" in algo_choice:
        desc_box.info("큐로 같은 깊이를 먼저 탐색합니다. 항상 최단 경로(최적해)를 보장하지만 메모리 사용량이 급증할 수 있습니다.")
        algo_key = "bfs"
    elif "언덕" in algo_choice:
        desc_box.info("맨해튼 거리가 줄어드는 방향으로만 이동합니다. 빠르지만 local optimum에 빠지면 해를 찾지 못합니다.")
        algo_key = "hc"
    elif "최고" in algo_choice:
        desc_box.info("맨해튼 거리가 낮은 상태를 우선 탐색합니다. 대부분 빠르게 해를 찾지만 최적해를 보장하지 않습니다.")
        algo_key = "bf"

    # 통계 테이블 데이터를 미리 보여주기 위한 가상 컨테이너들 생성
    metric_placeholder = st.empty()
    
    # 탐색 실행 및 실시간 애니메이션 루프
    if st.button("▶ 탐색 및 애니메이션 시각화 시작", type="primary", use_container_width=True):
        if not is_solvable(st.session_state.current_state):
            st.error("불가능한 퍼즐 배열입니다. 다시 섞어주세요.")
        else:
            start_time = time.time()
            algo_func = {"dfs": algo_dfs, "bfs": algo_bfs, "hc": algo_hc, "bf": algo_bf}[algo_key]
            path, nodes_count, is_failed = algo_func(st.session_state.current_state)
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # 해 탐색 자체를 완전히 패배한 경우 (예: 깊이 제한 초과 등)
            if path is None or (algo_key == "hc" and is_failed and len(path) <= 1):
                st.session_state.stats = {
                    "nodes": f"{nodes_count:,}", "moves": "실패", "time": f"{execution_time:.1f} ms",
                    "status": "✗ 해를 찾지 못했습니다 (Local Optimum 상태)."
                }
                with puzzle_placeholder.container():
                    draw_puzzle(st.session_state.current_state, is_failed=True)
                status_placeholder.error(st.session_state.stats["status"])
            else:
                moves_count = len(path) - 1
                
                # ⭐ 핵심 수정: st.rerun() 없이 컴포넌트 내부에서 애니메이션 순회 제어
                for step_idx, state in enumerate(path):
                    is_last = (step_idx == len(path) - 1)
                    
                    # 1. 메인 퍼즐판 그래픽 변경
                    with puzzle_placeholder.container():
                        draw_puzzle(state, is_solved=(state == GOAL), is_failed=(is_failed and is_last))
                    
                    # 2. 메시지 알림창 처리
                    if state == GOAL:
                        status_text = f"✓ 완료! {moves_count}번 이동 완료"
                        status_placeholder.success(status_text)
                    elif is_failed and is_last:
                        status_text = f"✗ 국소 최적해(Local Optimum)에 갇힘 — 최종 맨해튼 거리: {manhattan(state)}"
                        status_placeholder.error(status_text)
                    else:
                        status_text = f"탐색 애니메이션 재생 중... (Step {step_idx}/{moves_count})"
                        status_placeholder.warning(status_text)
                    
                    # 3. 실시간 결과 분석 스코어 보드 반영
                    with metric_placeholder.container():
                        st.divider()
                        st.subheader("결과 데이터 분석")
                        stat_cols = st.columns(3)
                        stat_cols[0].metric("탐색한 총 노드 수", f"{nodes_count:,}")
                        stat_cols[1].metric("최종 이동 횟수", f"{moves_count}번 후 실패" if is_failed and is_last else f"{step_idx} / {moves_count}번")
                        stat_cols[2].metric("알고리즘 연산 시간", f"{execution_time:.1f} ms")
                    
                    # 지정한 슬라이더 속도만큼 대기
                    time.sleep(speed_sec)
                
                # 최종 고정 데이터 세션에 박제
                st.session_state.stats = {
                    "nodes": f"{nodes_count:,}",
                    "moves": f"{moves_count}번 이동 후 실패" if is_failed else f"{moves_count}번",
                    "time": f"{execution_time:.1f} ms",
                    "status": status_text
                }
                # 마지막에 상태 유지를 위해 한 판 강제 리렌더링
                st.session_state.current_state = path[-1]

    # 기본(또는 탐색 완료 후) 메트릭 판 표시 구조
    with metric_placeholder.container():
        st.divider()
        st.subheader("결과 데이터 분석")
        stat_cols = st.columns(3)
        stat_cols[0].metric("탐색한 총 노드 수", st.session_state.stats["nodes"])
        stat_cols[1].metric("최종 이동 횟수", st.session_state.stats["moves"])
        stat_cols[2].metric("알고리즘 연산 시간", st.session_state.stats["time"])

    st.divider()
    st.subheader("목표 상태")
    for row in range(3):
        row_str = ""
        for col in range(3):
            val = GOAL[row*3 + col]
            row_str += f'<span class="goal-tile">{val if val!=0 else "_"}</span>'
        st.markdown(row_str, unsafe_allow_html=True)
