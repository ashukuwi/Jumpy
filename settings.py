class Settings:
    def __init__(self):
        self.WIDTH = 480
        self.HEIGHT = 800
        self.bg_color = (25, 100, 250)
        self.p_col = (0, 255, 0)

        self.player_speed = 5
        self.dirt_width = 100

        self.plat_list = [(self.WIDTH / 2, self.HEIGHT * 3 / 4 - 100),
                          (125, self.HEIGHT - 350),
                          (350, 200,),
                          (175, 100)]

        self.font_name = 'arial'
        self.friction = -0.1

        self.hs = "highscore.txt"
        self.spritesheet = "spritesheet_jumper.png"

        self.boost = 60
        self.find_boost = 2
        self.mobs = 5000