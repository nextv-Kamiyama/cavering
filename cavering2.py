import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np

# 頂点シェーダー：頂点の位置とテクスチャ座標を設定
vertex_shader = """
#version 120
attribute vec2 position;
varying vec2 uv;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    uv = (position + 1.0) * 0.5;  // テクスチャ座標を0-1の範囲に変換
}
"""

# フラグメントシェーダー：波紋エフェクトの計算と描画
fragment_shader = """
#version 120
uniform sampler2D texture;       // 背景テクスチャ
uniform float time;             // 現在の時間
varying vec2 uv;                // テクスチャ座標

// 複数の波紋情報を保持する配列
uniform vec2 ripple_positions[50];  // 波紋の位置
uniform float ripple_times[50];     // 波紋の生成時間
uniform int ripple_count;           // 現在の波紋数

void main() {
    vec2 p = uv * 2.0 - 1.0;        // 座標を-1から1の範囲に変換
    vec2 ripple = uv;               // 波紋による歪み効果の初期値
    float total_delta = 0.0;        // 全波紋の合計強度
    
    // 全ての波紋効果を計算して重ね合わせる
    for (int i = 0; i < ripple_count; i++) {
        vec2 ripple_pos = ripple_positions[i] * 2.0 - 1.0;
        float ripple_time = time - ripple_times[i];
        float len = length(p - ripple_pos);
        
        // 時間経過による波紋の減衰
        float strength = max(0.0, 1.0 - ripple_time * 2.0);
        // 波紋の強度を計算
        float delta = sin(len * 20.0 - ripple_time * 12.0) * 0.05 * strength;
        total_delta += delta;
        
        // 波紋による歪み効果を追加
        ripple += (p - ripple_pos) / len * cos(len * 20.0 - ripple_time * 12.0) * 0.01 * strength;
    }
    
    // 最終的な色を計算
    vec3 color = texture2D(texture, ripple).rgb;
    gl_FragColor = vec4(color + total_delta, 1.0);
}
"""

# 波紋の情報を保持するクラス
class RipplePoint:
    def __init__(self, pos, time):
        self.pos = pos    # 波紋の位置
        self.time = time  # 生成時間

# シェーダープログラムの作成
def create_shader_program():
    return compileProgram(
        compileShader(vertex_shader, GL_VERTEX_SHADER),
        compileShader(fragment_shader, GL_FRAGMENT_SHADER)
    )

# Pygameの初期化
pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

# 背景画像の読み込みとテクスチャの設定
background = pygame.image.load("AdobeStock_Cave.jpeg").convert()
background = pygame.transform.scale(background, display)
img_data = pygame.image.tostring(background, 'RGB', 1)

# OpenGLテクスチャの生成と設定
texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, display[0], display[1], 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

# シェーダープログラムの使用開始
shader = create_shader_program()
glUseProgram(shader)

# 頂点データの設定（画面全体を覆う四角形）
vertices = np.array([-1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0], dtype=np.float32)
vbo = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

# 頂点属性の設定
position = glGetAttribLocation(shader, "position")
glEnableVertexAttribArray(position)
glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 0, None)

# シェーダーのuniform変数の位置を取得
time_loc = glGetUniformLocation(shader, "time")
ripple_positions_loc = glGetUniformLocation(shader, "ripple_positions")
ripple_times_loc = glGetUniformLocation(shader, "ripple_times")
ripple_count_loc = glGetUniformLocation(shader, "ripple_count")

# ゲームループの初期設定
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()
ripple_points = []        # 波紋情報を格納するリスト
MAX_RIPPLES = 50         # 最大波紋数

# メインループ
while True:
    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        # マウスクリックまたはドラッグ時の波紋生成
        elif event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.MOUSEMOTION and event.buttons[0]):
            x, y = pygame.mouse.get_pos()
            current_time = (pygame.time.get_ticks() - start_time) / 1000.0
            mouse_pos = [x / display[0], 1 - y / display[1]]
            ripple_points.append(RipplePoint(mouse_pos, current_time))
            # 最大波紋数を超えた場合、古い波紋を削除
            if len(ripple_points) > MAX_RIPPLES:
                ripple_points.pop(0)

    # 画面クリア
    glClear(GL_COLOR_BUFFER_BIT)

    # 現在時刻の更新
    current_time = (pygame.time.get_ticks() - start_time) / 1000.0
    glUniform1f(time_loc, current_time)

    # 波紋データをシェーダーに送信
    positions = np.array([p.pos for p in ripple_points], dtype=np.float32).flatten()
    times = np.array([p.time for p in ripple_points], dtype=np.float32)
    
    glUniform2fv(ripple_positions_loc, len(ripple_points), positions)
    glUniform1fv(ripple_times_loc, len(ripple_points), times)
    glUniform1i(ripple_count_loc, len(ripple_points))

    # 描画実行
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

    # 画面更新
    pygame.display.flip()
    clock.tick(60)  # フレームレートを60FPSに制限