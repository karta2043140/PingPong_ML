# Import the necessary modules and classes
from mlgame.communication import ml as comm

scene = (200, 500)
ball = (5, 5)
platform = (40, 30)
blocker = (30, 20)

blocker_y = 240
platform_1P = 420
platform_2P = 80

def ml_loop(side: str):
    #init
    ballServeFrame = 0
    pre_blocker_x = 0
    blocker_speed = 0
    pre_ball_speed = 0  # y
    platform_x = 0
    platform_target = scene[0] / 2

    #start
    comm.ml_ready()
    while True:
        scene_info = comm.recv_from_game()
        if scene_info["status"] != "GAME_ALIVE":
            #reset

            #restart
            comm.ml_ready()
            continue

        #serveBall
        if scene_info["ball_speed"][1] == 0:
            ballServeFrame = scene_info["frame"]
            pre_blocker_x = scene_info["blocker"][0]
            if pre_blocker_x == 180:
                pre_blocker_x = 170
            pre_ball_speed = scene_info["ball_speed"][1]
            if scene_info["blocker"][0] == 80 and scene_info["blocker"][0] == 180:
                comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
            elif scene_info["blocker"][0] < 50 or (scene_info["blocker"][0] > 80 and scene_info["blocker"][0] < 150):
                comm.send_to_game({"frame": scene_info["frame"], "command": "SERVE_TO_LEFT"})
            else:
                comm.send_to_game({"frame": scene_info["frame"], "command": "SERVE_TO_RIGHT"})
            continue

        blocker_speed = scene_info["blocker"][0] - pre_blocker_x
        if blocker_speed == 0:
            blocker_speed = 5
        
        if side == "1P":
            platform_x = scene_info["platform_1P"][0] + platform[0] / 2
            if scene_info["ball"][1] + ball[1] + scene_info["ball_speed"][1] >= platform_1P:
                next_blocker_x = scene_info["blocker"][0] + blocker_speed
                next_blocker_speed = blocker_speed
                if next_blocker_x <= 0:
                    next_blocker_x = 0
                    next_blocker_speed = -next_blocker_speed
                elif next_blocker_x + blocker[0] >= scene[0]:
                    next_blocker_x = scene[0] - blocker[0]
                    next_blocker_speed = -next_blocker_speed
                next_ball_x = scene_info["ball"][0] + scene_info["ball_speed"][0]
                next_ball_speed = scene_info["ball_speed"][0]
                if next_ball_x <= 0:
                    next_ball_x = 0
                    next_ball_speed = -next_ball_speed
                elif next_ball_x + ball[0] >= scene[0]:
                    next_ball_x = scene[0] - ball[0]
                    next_ball_speed = -next_ball_speed
                if (scene_info["frame"] - ballServeFrame) % 100 == 0:
                    next_ball_speed = speed_up(next_ball_speed)
                a = ball_move_predict(scene_info["frame"] - ballServeFrame + 1, next_ball_x, platform_1P, next_ball_speed, -abs(next_ball_speed), next_blocker_x, next_blocker_speed)
                b = ball_move_predict(scene_info["frame"] - ballServeFrame + 1, next_ball_x, platform_1P, next_ball_speed + 3, -abs(next_ball_speed), next_blocker_x, next_blocker_speed)
                c = ball_move_predict(scene_info["frame"] - ballServeFrame + 1, next_ball_x, platform_1P, -next_ball_speed, -abs(next_ball_speed), next_blocker_x, next_blocker_speed)
                decide = (a, b, c)
                die = True
                ball_serve_type = 0
                block_distance = scene[0] * 2
                distance = 0
                for i in range(3):
                    if decide[i][0]:
                        if die and abs(decide[i][1] - platform_x) <= block_distance:
                            ball_serve_type = i
                            block_distance = abs(decide[i][1] - platform_x)
                    else:
                        die = False
                        if abs(decide[i][1] - (scene_info["platform_2P"][0] + platform[0] / 2)) >= distance:
                            ball_serve_type = i
                            distance = abs(decide[i][1] - (scene_info["platform_2P"][0] + platform[0] / 2))
                pre_blocker_x = scene_info["blocker"][0]
                pre_ball_speed = scene_info["ball_speed"][1]
                if scene_info["ball_speed"][0] < 0:
                    if platform_target < platform_x - platform[0] / 2 or (ball_serve_type == 1 and platform_target <= platform_x + (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
                    elif platform_target > platform_x + platform[0] / 2 or (ball_serve_type == 2 and platform_target >= platform_x - (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})
                    else:
                        comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
                else:
                    if platform_target > platform_x + platform[0] / 2 or (ball_serve_type == 1 and platform_target >= platform_x - (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})
                    elif platform_target < platform_x - platform[0] / 2 or (ball_serve_type == 2 and platform_target <= platform_x + (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
                    else:
                        comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
                continue
            elif scene_info["ball_speed"][1] > 0 and pre_ball_speed <= 0: #my
                temp = ball_move_predict(scene_info["frame"] - ballServeFrame, scene_info["ball"][0], scene_info["ball"][1], scene_info["ball_speed"][0], scene_info["ball_speed"][1], scene_info["blocker"][0], blocker_speed)
                if temp[0]:
                    platform_target = predict(temp[2], temp[3], temp[4], temp[5], temp[6], temp[7], temp[8])
                else:
                    platform_target = temp[1]
            elif scene_info["ball_speed"][1] < 0 and pre_ball_speed >= 0: #enemy
                temp = ball_move_predict(scene_info["frame"] - ballServeFrame, scene_info["ball"][0], scene_info["ball"][1], scene_info["ball_speed"][0], scene_info["ball_speed"][1], scene_info["blocker"][0], blocker_speed)
                if temp[0]:
                    platform_target = temp[1]
                else:
                    platform_target = predict(temp[2], temp[3], temp[4], temp[5], temp[6], temp[7], temp[8])
        else:
            platform_x = scene_info["platform_2P"][0] + platform[0] / 2
            if scene_info["ball"][1] + scene_info["ball_speed"][1] <= platform_2P:
                next_blocker_x = scene_info["blocker"][0] + blocker_speed
                next_blocker_speed = blocker_speed
                if next_blocker_x <= 0:
                    next_blocker_x = 0
                    next_blocker_speed = -next_blocker_speed
                elif next_blocker_x + blocker[0] >= scene[0]:
                    next_blocker_x = scene[0] - blocker[0]
                    next_blocker_speed = -next_blocker_speed
                next_ball_x = scene_info["ball"][0] + scene_info["ball_speed"][0]
                next_ball_speed = scene_info["ball_speed"][0]
                if next_ball_x <= 0:
                    next_ball_x = 0
                    next_ball_speed = -next_ball_speed
                elif next_ball_x + ball[0] >= scene[0]:
                    next_ball_x = scene[0] - ball[0]
                    next_ball_speed = -next_ball_speed
                if (scene_info["frame"] - ballServeFrame) % 100 == 0:
                    next_ball_speed = speed_up(next_ball_speed)
                a = ball_move_predict(scene_info["frame"] - ballServeFrame + 1, next_ball_x, platform_1P, next_ball_speed, abs(next_ball_speed), next_blocker_x, next_blocker_speed)
                b = ball_move_predict(scene_info["frame"] - ballServeFrame + 1, next_ball_x, platform_1P, next_ball_speed + 3, abs(next_ball_speed), next_blocker_x, next_blocker_speed)
                c = ball_move_predict(scene_info["frame"] - ballServeFrame + 1, next_ball_x, platform_1P, -next_ball_speed, abs(next_ball_speed), next_blocker_x, next_blocker_speed)
                decide = (a, b, c)
                die = True
                ball_serve_type = 0
                block_distance = scene[0] * 2
                distance = 0
                for i in range(3):
                    if decide[i][0]:
                        if die and abs(decide[i][1] - platform_x) <= block_distance:
                            ball_serve_type = i
                            block_distance = abs(decide[i][1] - platform_x)
                    else:
                        die = False
                        if abs(decide[i][1] - (scene_info["platform_1P"][0] + platform[0] / 2)) >= distance:
                            ball_serve_type = i
                            distance = abs(decide[i][1] - (scene_info["platform_1P"][0] + platform[0] / 2))
                pre_blocker_x = scene_info["blocker"][0]
                pre_ball_speed = scene_info["ball_speed"][1]
                if scene_info["ball_speed"][0] < 0:
                    if platform_target < platform_x - platform[0] / 2 or (ball_serve_type == 1 and platform_target <= platform_x + (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
                    elif platform_target > platform_x + platform[0] / 2 or (ball_serve_type == 2 and platform_target >= platform_x - (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})
                    else:
                        comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
                else:
                    if platform_target > platform_x + platform[0] / 2 or (ball_serve_type == 1 and platform_target >= platform_x - (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})
                    elif platform_target < platform_x - platform[0] / 2 or (ball_serve_type == 2 and platform_target <= platform_x + (platform[0] / 2 - 5)):
                        comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
                    else:
                        comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
                continue
            elif scene_info["ball_speed"][1] < 0 and pre_ball_speed >= 0:
                temp = ball_move_predict(scene_info["frame"] - ballServeFrame, scene_info["ball"][0], scene_info["ball"][1], scene_info["ball_speed"][0], scene_info["ball_speed"][1], scene_info["blocker"][0], blocker_speed)
                if temp[0]:
                    platform_target = predict(temp[2], temp[3], temp[4], temp[5], temp[6], temp[7], temp[8])
                else:
                    platform_target = temp[1]
            elif scene_info["ball_speed"][1] > 0 and pre_ball_speed <= 0:
                temp = ball_move_predict(scene_info["frame"] - ballServeFrame, scene_info["ball"][0], scene_info["ball"][1], scene_info["ball_speed"][0], scene_info["ball_speed"][1], scene_info["blocker"][0], blocker_speed)
                if temp[0]:
                    platform_target = temp[1]
                else:
                    platform_target = predict(temp[2], temp[3], temp[4], temp[5], temp[6], temp[7], temp[8])

        pre_blocker_x = scene_info["blocker"][0]
        pre_ball_speed = scene_info["ball_speed"][1]

        if platform_x == platform_target:
            comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
        elif platform_x - platform_target > 0:
            comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
        else:
            comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})

def predict(frame: int, pos_x: int, pos_y: int, speed_x: int, speed_y: int, blocker_pos: int, blocker_speed: int):
    min_x = scene[0] * 2
    max_x = -scene[0] * 2
    a = ball_move_predict(frame, pos_x, pos_y, speed_x, speed_y, blocker_pos, blocker_speed)
    b = ball_move_predict(frame, pos_x, pos_y, speed_x + 3, speed_y, blocker_pos, blocker_speed)
    c = ball_move_predict(frame, pos_x, pos_y, -speed_x, speed_y, blocker_pos, blocker_speed)
    predict_temp = (a, b, c)
    for i in range(3):
        if not predict_temp[i][0]:
            if predict_temp[i][1] < min_x:
                min_x = predict_temp[i][1]
            if predict_temp[i][1] > max_x:
                max_x = predict_temp[i][1]
    if max_x < 0:
        return scene[0] / 2
    return (min_x + max_x) / 2
            
def ball_move_predict(frame: int, pos_x: int, pos_y: int, speed_x: int, speed_y: int, blocker_pos: int, blocker_speed: int):
    block = False
    pre_speed = (speed_x, speed_y)
    end = 0
    if speed_y < 0:
        while pos_y > platform_2P:
            blocker_pos = blocker_pos + blocker_speed
            if blocker_pos <= 0:
                blocker_pos = 0
                blocker_speed = -blocker_speed
            elif blocker_pos + blocker[0] > scene[0]:
                blocker_pos = scene[0] - blocker[0]
                blocker_speed = -blocker_speed
            pre_x = pos_x
            pre_y = pos_y
            pre_speed = (speed_x, speed_y)
            pos_x = pos_x + speed_x
            pos_y = pos_y + speed_y
            if pre_y > blocker_y + blocker[1] and pos_y <= blocker_y + blocker[1]:
                pos = pos_x - speed_x * (pos_y - blocker_y + blocker[1]) / speed_y + ball[0] / 2
                if pos <= blocker_pos + blocker[0] and pos >= blocker_pos:
                    block = True
                    end = blocker_y + blocker[1]
                    pos_y = end + ball[1]
                    speed_y = -speed_y
                    if pos_x <= 0:
                        pos_x = 0
                        speed_x = -speed_x
                    elif pos_x + ball[0] >= scene[0]:
                        pos_x = scene[0] - ball[0]
                        speed_x = -speed_x
                    if (frame % 100) == 0:
                        speed_x = speed_up(speed_x)
                        speed_y = speed_y + 1
                    frame = frame + 1
                    while pos_y < platform_1P:
                        blocker_pos = blocker_pos + blocker_speed
                        if blocker_pos <= 0:
                            blocker_pos = 0
                            blocker_speed = -blocker_speed
                        elif blocker_pos + blocker[0] > scene[0]:
                            blocker_pos = scene[0] - blocker[0]
                            blocker_speed = -blocker_speed
                        pre_speed = (speed_x, speed_y)
                        pos_x = pos_x + speed_x
                        pos_y = pos_y + speed_y
                        if pos_x <= 0:
                            pos_x = 0
                            speed_x = -speed_x
                        elif pos_x + ball[0] >= scene[0]:
                            pos_x = scene[0] - ball[0]
                            speed_x = -speed_x
                        if (frame % 100) == 0:
                            speed_x = speed_up(speed_x)
                            speed_y = speed_y + 1
                        frame = frame + 1
                    end = platform_1P - ball[1]
                    break
            if pre_x + ball[0] < blocker_pos and pos_x + ball[0] >= blocker_pos:
                pos = pos_y - speed_y * (pos_x - blocker_pos) / speed_x + ball[1] / 2
                if pos <= blocker_y + blocker[1] and pos >= blocker_y:
                    pos_x = blocker_pos - ball[0]
                    speed_x = -speed_x
            elif pre_x > blocker_pos + blocker[0] and pos_x <= blocker_pos + blocker[0]:
                pos = pos_y - speed_y * (pos_x - (blocker_pos + blocker[0])) / speed_x + ball[1] / 2
                if pos <= blocker_y + blocker[1] and pos >= blocker_y:
                    pos_x = blocker_pos + blocker[0]
                    speed_x = -speed_x
            if pos_x <= 0:
                pos_x = 0
                speed_x = -speed_x
            elif pos_x + ball[0] >= scene[0]:
                pos_x = scene[0] - ball[0]
                speed_x = -speed_x
            if (frame % 100) == 0:
                speed_x = speed_up(speed_x)
                speed_y = speed_y - 1
            frame = frame + 1
            end = platform_2P
    else:
        pos_y = pos_y + ball[1]
        while pos_y < platform_1P:
            blocker_pos = blocker_pos + blocker_speed
            if blocker_pos <= 0:
                blocker_pos = 0
                blocker_speed = -blocker_speed
            elif blocker_pos + blocker[0] > scene[0]:
                blocker_pos = scene[0] - blocker[0]
                blocker_speed = -blocker_speed
            pre_x = pos_x
            pre_y = pos_y
            pre_speed = (speed_x, speed_y)
            pos_x = pos_x + speed_x
            pos_y = pos_y + speed_y
            if pre_y < blocker_y and pos_y >= blocker_y:
                pos = pos_x - speed_x * (pos_y - blocker_y) / speed_y + ball[0] / 2
                if pos <= blocker_pos + blocker[0] and pos >= blocker_pos:
                    block = True
                    end = blocker_y - ball[1]
                    pos_y = end
                    speed_y = -speed_y
                    if pos_x <= 0:
                        pos_x = 0
                        speed_x = -speed_x
                    elif pos_x + ball[0] >= scene[0]:
                        pos_x = scene[0] - ball[0]
                        speed_x = -speed_x
                    if (frame % 100) == 0:
                        speed_x = speed_up(speed_x)
                        speed_y = speed_y + 1
                    frame = frame + 1
                    while pos_y > platform_2P:
                        blocker_pos = blocker_pos + blocker_speed
                        if blocker_pos <= 0:
                            blocker_pos = 0
                            blocker_speed = -blocker_speed
                        elif blocker_pos + blocker[0] > scene[0]:
                            blocker_pos = scene[0] - blocker[0]
                            blocker_speed = -blocker_speed
                        pre_speed = (speed_x, speed_y)
                        pos_x = pos_x + speed_x
                        pos_y = pos_y + speed_y
                        if pos_x <= 0:
                            pos_x = 0
                            speed_x = -speed_x
                        elif pos_x + ball[0] >= scene[0]:
                            pos_x = scene[0] - ball[0]
                            speed_x = -speed_x
                        if (frame % 100) == 0:
                            speed_x = speed_up(speed_x)
                            speed_y = speed_y - 1
                        frame = frame + 1
                    end = platform_2P
                    break
            if pre_x + ball[0] < blocker_pos and pos_x + ball[0] >= blocker_pos:
                pos = pos_y - speed_y * (pos_x - blocker_pos) / speed_x - ball[1] / 2
                if pos <= blocker_y + blocker[1] and pos >= blocker_y:
                    pos_x = blocker_pos - ball[0]
                    speed_x = -speed_x
            elif pre_x > blocker_pos + blocker[0] and pos_x <= blocker_pos + blocker[0]:
                pos = pos_y - speed_y * (pos_x - (blocker_pos + blocker[0])) / speed_x - ball[1] / 2
                if pos <= blocker_y + blocker[1] and pos >= blocker_y:
                    pos_x = blocker_pos + blocker[0]
                    speed_x = -speed_x
            if pos_x <= 0:
                pos_x = 0
                speed_x = -speed_x
            elif pos_x + ball[0] >= scene[0]:
                pos_x = scene[0] - ball[0]
                speed_x = -speed_x
            if (frame % 100) == 0:
                speed_x = speed_up(speed_x)
                speed_y = speed_y + 1
            frame = frame + 1
            end = platform_1P - ball[1]
    pos = pos_x - pre_speed[0] * (pos_y - end) / pre_speed[1] + ball[0] / 2
    return (block, pos, frame, pos_x, end, speed_x, -speed_y, blocker_pos, blocker_speed)

def speed_up(speed: int):
    if speed < 0:
        return speed - 1
    return speed + 1
