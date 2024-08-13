# スイカゲームプレイ用の環境
# Stateはcv2.VideoCapture(2)で取得した画像
# Actionは
import time

import cv2
import easyocr
import torch

from Commands.Keys import KeyPress, Button, Hat, Direction, Stick
from utils import Sender

COMPORT = 3
SCORE_XMIN, SCORE_YMIN, SCORE_XMAX, SCORE_YMAX = 150, 160, 400, 260
RING_EVOLUTION_XMIN, RING_EVOLUTION_YMIN, RING_EVOLUTION_XMAX, RING_EVOLUTION_YMAX = 1400, 500, 1850, 1000
RING_EVOLUTION_THRESHOLD = 400000000
RANKIN_TEXT_XMIN, RANKIN_TEXT_YMIN, RANKIN_TEXT_XMAX, RANKIN_TEXT_YMAX = 600, 200, 1300, 300
RANKIN_TEXT_XMIN_2, RANKIN_TEXT_YMIN_2, RANKIN_TEXT_XMAX_2, RANKIN_TEXT_YMAX_2 = 250, 150, 1100, 250
GAMEOVER_TEXT_XMIN, GAMEOVER_TEXT_YMIN, GAMEOVER_TEXT_XMAX, GAMEOVER_TEXT_YMAX = 400, 150, 1000, 220
RANKIN_THRESHOLD = 100000000
RANKIN_THRESHOLD_2 = 100000000
GAMEOVER_THRESHOLD = 100000000
INIT_TEXT_XMIN, INIT_TEXT_YMIN, INIT_TEXT_XMAX, INIT_TEXT_YMAX = 400, 320, 1500, 420
INIT_TEXT_THRESHOLD = 100000000
OBSERVE_XMIN, OBSERVE_YMIN, OBSERVE_XMAX, OBSERVE_YMAX = 550, 50, 1750, 1050
OBSERVE_SIZE = (120, 100)


class SuikaEnv:
    def __init__(self):

        self.rankin_text_image = cv2.imread("template_images/rankin_text_image.png")
        self.rankin_text_image_2 = cv2.imread("template_images/rankin_text_image_2.jpg")
        self.gameover_text_image = cv2.imread("template_images/gameover_text_image.png")
        self.init_text_image = cv2.imread("template_images/init_text_image.png")
        self.ring_evolution_image = cv2.imread("template_images/ring_evolution.jpg")
        self.rankin_text_image = self.rankin_text_image[:, :, ::-1]
        self.rankin_text_image_2 = self.rankin_text_image_2[:, :, ::-1]
        self.gameover_text_image = self.gameover_text_image[:, :, ::-1]
        self.init_text_image = self.init_text_image[:, :, ::-1]
        self.ring_evolution_image = self.ring_evolution_image[:, :, ::-1]
        self.reader = easyocr.Reader(['en'])
        ser = Sender(False)
        ser.openSerial(COMPORT)
        self.key = KeyPress(ser)

        self.cap = cv2.VideoCapture(2)
        self.cap.set(3, 1920)
        self.cap.set(4, 1080)
        self.reader = easyocr.Reader(['en'])
        self.current_score = self.get_score()

    
    def step(self, action):
        if action == 0:
            # Aを押す
            self.key.input([Button.A])
            time.sleep(0.1)
            self.key.inputEnd([Button.A])
            time.sleep(1)
        elif action == 1:
            # 左を押す
            self.key.input([Hat.LEFT])
            time.sleep(0.1)
            self.key.inputEnd([Hat.LEFT])
        elif action == 2:
            # 右を押す
            self.key.input([Hat.RIGHT])
            time.sleep(0.1)
            self.key.inputEnd([Hat.RIGHT])
        else:
            raise ValueError('action must be 0, 1 or 2')

        # 点数の取得
        score = self.get_score()
        if score >= 0:
            reward = score - self.current_score
            if 0 < reward < 500: # スイカゲームの仕様上1秒間に500点以上増えることは通常ない
                self.current_score = score
            else:
                reward = 0
        else:
            reward = 0
        
        #if action == 0:
        #    pass
        #else:
        #    reward -= 0.1
        
        #reward -= 0.1

        # 終了判定を行う
        done = self.is_done()

        # 観測の取得
        obs = self.get_observation()

        info = {
            "score": self.current_score,
        }
        return obs, reward, done, info

    def reset(self):
        # stateを初期化
        obs = self.get_observation()
        self.current_score = self.get_score()

        return obs
    
    def return_to_game(self):
        game_state = self.is_which_state()

        while game_state != "Playing":
            if game_state == "Rankin":
                # Aを押して1秒待機
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                time.sleep(2)
                # 左を押す
                self.key.input([Hat.LEFT])
                time.sleep(0.2)
                self.key.inputEnd([Hat.LEFT])
                # Aを押す
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                time.sleep(3)
            elif game_state == "Rankin_2":
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                time.sleep(2)
                # 左を押す
                self.key.input([Hat.LEFT])
                time.sleep(0.2)
                self.key.inputEnd([Hat.LEFT])
                # Aを押す
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                time.sleep(3)
            elif game_state == "Gameover":
                # 左を押す
                self.key.input([Hat.LEFT])
                time.sleep(1)
                self.key.inputEnd([Hat.LEFT])
                # Aを押す
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                time.sleep(3)
            elif game_state == "Init":
                self.key.input([Button.L, Button.R])
                time.sleep(6)
                self.key.inputEnd([Button.L, Button.R])
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                self.key.input([Button.A])
                time.sleep(0.1)
                self.key.inputEnd([Button.A])
                time.sleep(3)
            time.sleep(1)
            #frame = self.get_frame() # get_frame()を空打ちしないと取得できるカメラ画像が更新されていないことがある（？）
            game_state = self.is_which_state()
    
    def is_done(self):
        # 現在の画面が状態かを判定するメソッド
        frame = self.get_frame()
        # 通常のプレイ画面かどうかの判定
        res = cv2.matchTemplate(
             frame[RING_EVOLUTION_YMIN:RING_EVOLUTION_YMAX, RING_EVOLUTION_XMIN:RING_EVOLUTION_XMAX, :], 
             self.ring_evolution_image, 
             cv2.TM_CCOEFF
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > RING_EVOLUTION_THRESHOLD:
            return False
        else:
            return True
    
    def is_which_state(self):
        # 現在の画面が状態かを判定するメソッド
        frame = self.get_frame()
        # 通常のプレイ画面かどうかの判定
        res = cv2.matchTemplate(
             frame[RING_EVOLUTION_YMIN:RING_EVOLUTION_YMAX, RING_EVOLUTION_XMIN:RING_EVOLUTION_XMAX, :], 
             self.ring_evolution_image, 
             cv2.TM_CCOEFF
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > RING_EVOLUTION_THRESHOLD:
            return "Playing"

        # ランキングイン画面かどうかの判定
        res = cv2.matchTemplate(
             frame[RANKIN_TEXT_YMIN:RANKIN_TEXT_YMAX, RANKIN_TEXT_XMIN:RANKIN_TEXT_XMAX, :], 
             self.rankin_text_image, 
             cv2.TM_CCOEFF
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > RANKIN_THRESHOLD:
            return "Rankin"
        
        # もう一つのランキングイン画面かどうかの判定
        res = cv2.matchTemplate(
             frame[RANKIN_TEXT_YMIN_2:RANKIN_TEXT_YMAX_2, RANKIN_TEXT_XMIN_2:RANKIN_TEXT_XMAX_2, :],
             self.rankin_text_image_2, 
             cv2.TM_CCOEFF
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > RANKIN_THRESHOLD_2:
            return "Rankin_2"

        # ゲームオーバー画面かどうかの判定
        res = cv2.matchTemplate(
             frame[GAMEOVER_TEXT_YMIN:GAMEOVER_TEXT_YMAX, GAMEOVER_TEXT_XMIN:GAMEOVER_TEXT_XMAX, :], 
             self.gameover_text_image, 
             cv2.TM_CCOEFF
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > GAMEOVER_THRESHOLD:
            return "Gameover"
        
        res = cv2.matchTemplate(
                frame, 
                self.init_text_image, 
                cv2.TM_CCOEFF
            )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > INIT_TEXT_THRESHOLD:
            return "Init"

        return None
    
    def get_score(self):
        # 現在のスコアを取得するメソッド
        frame = self.get_frame()
        score_image = frame[SCORE_YMIN:SCORE_YMAX, SCORE_XMIN:SCORE_XMAX, :]
        text = self.reader.readtext(score_image)
        try:
            score = int(text[0][1])
        except:
            score = -1
        return score

    def get_frame(self, discard_frame=3):
        for _ in range(discard_frame):
            self.cap.read()
        # 現在のフレームを取得するメソッド
        ret, frame = self.cap.read()
        if not ret:
            raise ValueError('frame is None')
        frame = frame[:, :, ::-1]
        return frame
    
    def get_observation(self):
        frame = self.get_frame()
        obs = frame[OBSERVE_YMIN:OBSERVE_YMAX, OBSERVE_XMIN:OBSERVE_XMAX, :]
        obs = cv2.resize(obs, OBSERVE_SIZE, interpolation=cv2.INTER_LINEAR) / 255.0
        return torch.FloatTensor(obs).permute(2, 0, 1).unsqueeze(0)
