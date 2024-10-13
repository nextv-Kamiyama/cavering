import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np

vertex_shader = """
#version 120
attribute vec2 position;
varying vec2 uv;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    uv = (position + 1.0) * 0.5;
}
"""

fragment_shader = """
#version 120
uniform sampler2D texture;
uniform float time;
uniform vec2 mouse_pos;
uniform float click_time;
varying vec2 uv;

void main() {
    vec2 p = uv * 2.0 - 1.0;
    float len = length(p);
    
    // 基本の波紋
    vec2 ripple = uv + (p/len)*cos(len*12.0-time*4.0)*0.03;
    
    // クリックによる波紋
    vec2 click_p = mouse_pos * 2.0 - 1.0;
    float click_len = length(p - click_p);
    float click_strength = max(0.0, 1.0 - (time - click_time) * 2.0);
    ripple += (p-click_p)/click_len * cos(click_len*20.0 - (time-click_time)*10.0) * 0.05 * click_strength;
    
    float delta = 0.05 * sin(len*12.0-time*4.0);
    delta += 0.1 * sin(click_len*20.0 - (time-click_time)*10.0) * click_strength;
    
    vec3 color = texture2D(texture, ripple).rgb;
    gl_FragColor = vec4(color + delta, 1.0);
}
"""

def create_shader_program():
    return compileProgram(
        compileShader(vertex_shader, GL_VERTEX_SHADER),
        compileShader(fragment_shader, GL_FRAGMENT_SHADER)
    )

pygame.init()
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

background = pygame.image.load("AdobeStock_Cave.jpeg").convert()
background = pygame.transform.scale(background, display)
img_data = pygame.image.tostring(background, 'RGB', 1)

texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, display[0], display[1], 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

shader = create_shader_program()
glUseProgram(shader)

vertices = np.array([-1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0], dtype=np.float32)
vbo = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

position = glGetAttribLocation(shader, "position")
glEnableVertexAttribArray(position)
glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 0, None)

time_loc = glGetUniformLocation(shader, "time")
mouse_pos_loc = glGetUniformLocation(shader, "mouse_pos")
click_time_loc = glGetUniformLocation(shader, "click_time")

clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()
last_click_time = 0
mouse_pos = [0.5, 0.5]

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION and event.buttons[0]:
            x, y = pygame.mouse.get_pos()
            mouse_pos = [x / display[0], 1 - y / display[1]]
            last_click_time = (pygame.time.get_ticks() - start_time) / 1000.0

    glClear(GL_COLOR_BUFFER_BIT)

    current_time = (pygame.time.get_ticks() - start_time) / 1000.0
    glUniform1f(time_loc, current_time)
    glUniform2f(mouse_pos_loc, mouse_pos[0], mouse_pos[1])
    glUniform1f(click_time_loc, last_click_time)

    glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

    pygame.display.flip()
    clock.tick(60)