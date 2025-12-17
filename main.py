import pygame
import random
import time
import json
import os
import sys
import math

WORDS = {
    "hit": ["strike", "slash", "blade", "fight", "steel", "enemy", "sword", "power"],
    "crit": ["shatter", "destroy", "lethal", "victory", "execute", "deadly", "fury"],
    "shield": ["guard", "shield", "block", "wall", "armor", "defend", "cover"],
    "heal": ["light", "mercy", "potion", "health", "spirit", "mending", "remedy"]
}
# 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ И КОНСТАНТЫ
WIDTH, HEIGHT = 1000, 650
FPS = 60
SAVE_FILE = "keystorm_ultimate_save.json"
IMG_FOLDER = "img"
SND_FOLDER = "snd"


# ЦВЕТОВАЯ ПАЛИТРА (РАСШИРЕННАЯ)
C_BG = (10, 10, 18)
C_BG_LHT = (25, 25, 40)
C_WHITE = (240, 240, 240)
C_RED = (255, 60, 60)
C_DARK_RED = (120, 0, 0)
C_GREEN = (60, 255, 100)
C_DARK_GREEN = (0, 100, 40)
C_GOLD = (255, 215, 0)
C_BLUE = (0, 191, 255)
C_PURPLE = (160, 32, 240)
C_GRAY = (100, 100, 110)
C_DARK_GRAY = (40, 40, 50)
C_BLACK = (0, 0, 0)
C_ORANGE = (255, 140, 0)

# ИНИЦИАЛИЗАЦИЯ
pygame.init()
FONT = pygame.font.SysFont("arial", 28)
FONT_SM = pygame.font.SysFont("arial", 18)

pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("KEYSTORM")
clock = pygame.time.Clock()


# ШРИФТЫ (С ПРОВЕРКОЙ)
def get_font(name, size, bold=False):
    try: return pygame.font.SysFont(name, size, bold=bold)
    except: return pygame.font.Font(None, size)

F_UI = get_font("consolas", 18)
F_MAIN = get_font("consolas", 24, True)
F_BOLD = get_font("consolas", 32, True)
F_BIG = get_font("impact", 80)
F_DESC = get_font("arial", 16)

# 2. БАЗЫ ДАННЫХ (СЛОВА, КЛАССЫ, ВРАГИ)
WORDS_DATABASE = {
    "hit": {
        1: ["hit", "tap", "cut", "jab", "dot", "stab", "bit", "low"],
        2: ["strike", "slash", "punch", "kick", "smack", "swing", "break", "crush"],
        3: ["impact", "assault", "cleave", "pierce", "damage", "pummel", "destroy", "ravage"]
    },
    "crit": {
        1: ["pow", "bam", "zap", "crit"],
        2: ["shatter", "burst", "splat", "wreck", "blast"],
        3: ["obliterate", "annihilate", "devastate", "extirpate", "shredder"]
    },
    "shield": {
        1: ["ward", "stop", "safe"],
        2: ["guard", "parry", "shell", "block", "cover"],
        3: ["fortress", "bulwark", "barrier", "defense", "rampart"]
    },
    "heal": ["heal", "cure", "mend", "life", "faith", "remedy", "regen", "bless", "spirit"]
}

CLASSES_DATA = {
    "WARRIOR": {
        "hp": 180, "atk": 12, "def": 5, "crit_c": 0.05, 
        "color": C_RED, "desc": "Мастер ближнего боя. Огромный запас здоровья и брони. Идеален для новичков."
    },
    "MAGE": {
        "hp": 90, "atk": 32, "def": 0, "crit_c": 0.12, 
        "color": C_BLUE, "desc": "Повелитель стихий. Хрупкое тело, но колоссальный урон. Требует скорости."
    },
    "ROGUE": {
        "hp": 120, "atk": 18, "def": 1, "crit_c": 0.40, 
        "color": C_GREEN, "desc": "Теневой убийца. Каждое второе слово может стать критическим ударом."
    }
}

# 3. СИСТЕМНЫЕ МОДУЛИ (VFX, ЗВУК, СПРАЙТЫ)
class SoundEngine:
    def __init__(self):
        self.library = {}
        if not os.path.exists(SND_FOLDER): os.makedirs(SND_FOLDER)
        self.load_sounds()

    def load_sounds(self):
        keys = ["hit", "crit", "heal", "death", "lvlup", "buy", "click", "error"]
        for k in keys:
            path = os.path.join(SND_FOLDER, f"{k}.wav")
            if os.path.exists(path):
                try: self.library[k] = pygame.mixer.Sound(path)
                except: self.library[k] = None
            else: self.library[k] = None

    def play(self, key):
        if key in self.library and self.library[key]:
            self.library[key].play()
class ParticleSystem:
    def __init__(self, x, y, color):
        self.particles = []
        for _ in range(15):
            self.particles.append({
                "x": x, "y": y,
                "vx": random.uniform(-6, 6), "vy": random.uniform(-6, 6),
                "life": 1.0, "color": color, "size": random.randint(2, 6)
            })

    def update(self, dt):
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.1 # Гравитация
            p["life"] -= dt * 1.5
            if p["life"] <= 0: 
                self.particles.remove(p)

    def draw(self, surf):
        for p in self.particles:
            alpha = int(255 * p["life"])
            s = pygame.Surface((p["size"]*2, p["size"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["color"], alpha), (p["size"], p["size"]), p["size"])
            surf.blit(s, (p["x"], p["y"]))

class FloatingText:
    def __init__(self, x, y, text, color, is_big=False):
        self.x, self.y = x, y
        self.text = text; self.color = color; self.life = 1.2
        self.is_big = is_big; self.offset_y = 0

    def update(self, dt):
        self.offset_y -= 60 * dt; self.life -= dt

    def draw(self, surf):
        font = F_BIG if self.is_big else F_BOLD
        rend = font.render(self.text, True, self.color)
        rend.set_alpha(int(255 * (self.life / 1.2)))
        surf.blit(rend, (self.x, self.y + self.offset_y))

# 4. ЯДРО ИГРЫ (GAME MANAGER)
class GameCore:
    def draw_class_select(self, surf):
        surf.fill(C_BG)
        mouse_pos = pygame.mouse.get_pos()
        
        title = F_BOLD.render("ВЫБЕРИТЕ ГЕРОЯ", True, C_GOLD)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        for i, (c_name, data) in enumerate(CLASSES_DATA.items()):
            # Базовый прямоугольник
            base_rect = pygame.Rect(80 + (i * 300), 150, 260, 400)
            
            # Анимация: если мышь наведена, rect смещается вверх
            is_hovered = base_rect.collidepoint(mouse_pos)
            y_pos = 150 - 20 if is_hovered else 150
            rect = pygame.Rect(80 + (i * 300), y_pos, 260, 400)
            
            # Цвет рамки
            color = data["color"] if is_hovered else C_DARK_GRAY
            
            # Рисуем карточку
            pygame.draw.rect(surf, C_BG_LHT, rect, border_radius=15)
            pygame.draw.rect(surf, color, rect, 3 if is_hovered else 1, border_radius=15)
            
            # Имя класса
            name_txt = F_BOLD.render(c_name, True, color)
            surf.blit(name_txt, (rect.x + 20, rect.y + 20))
            
            # Статы
            stats = [f"HP: {data['hp']}", f"ATK: {data['atk']}"]
            for j, s in enumerate(stats):
                surf.blit(F_UI.render(s, True, C_WHITE), (rect.x + 20, rect.y + 70 + (j*25)))

        hint = F_UI.render("Нажми 1, 2 или 3 на клавиатуре", True, C_GRAY)
        surf.blit(hint, (WIDTH//2 - hint.get_width()//2, 600))
    def __init__(self):
        self.state = "MENU"
        self.sounds = SoundEngine()
        self.load_sprites()
        self.vfx_particles = []
        self.vfx_texts = []
        self.screen_shake = 0
        self.screen_flash = 0
        self.flash_color = C_WHITE
        
        self.init_player_data()
        self.load_save()
        
        self.enemy = None
        self.active_words = {}
        self.typed_buffer = ""
        self.combo_count = 0
        self.heal_timer = 0
        self.heal_cooldown = 15.0
        self.player_input_name = self.player.get("name", "")

    def init_player_data(self):
        self.player = {
            "name": "Герой",
            "class": None,
            "hp": 100,
            "max_hp": 100,
            "energy": 0,
            "max_energy": 100,
            "gold": 0,
            "lvl": 1,
            "xp": 0,
            "stage": 1,
            "potions": 1,
            "atk_bonus": 10,
            "crit_chance": 0.05,
            
            
            # НОВОЕ: СИСТЕМА ПРОКАЧКИ
            "weapon_lvl": 1,   # Уровень меча
            "armor_lvl": 0,    # Уровень брони (0 - нет брони)
            "base_def": 0,     # Защита (поглощение урона)
            "total_dmg": 0,
            "diff_mult": 1.0,  # Множитель сложности
            "diff_name": "NORMAL",
            "total_dmg": 0,
            "kills": 0
        }
    def init_class(self, class_name):
        data = CLASSES_DATA[class_name]
        self.player["class"] = class_name
        self.player["max_hp"] = data["hp"]
        self.player["hp"] = data["hp"]
        self.player["atk_bonus"] = data["atk"]
        self.player["crit_chance"] = data["crit_c"]


    def load_save(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.player.update(data)
            except Exception as e:
                print(f"Ошибка загрузки: {e}")

    def save_progress(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.player, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    # ЛОГИКА БИТВЫ
    def start_new_battle(self):
        stg = self.player["stage"]
        is_boss = (stg % 5 == 0)
        
        # Параметры врага зависят от уровня игрока и стадии
        hp_mult = 2.5 if is_boss else 1.0
        atk_mult = 1.5 if is_boss else 1.0
        
        hp = int((100 + (stg * 50)) * hp_mult)
        atk = int((8 + (stg * 4)) * atk_mult)
        
        enemy_type = "boss" if is_boss else random.choice(["skeleton", "slime"])

        self.enemy = {
            "name": f"ВЕЛИКИЙ БОСС {stg}" if is_boss else enemy_type.upper(),
            "hp": hp,
            "max_hp": hp,
            "atk": atk,
            "color": C_PURPLE if is_boss else C_RED,
            "sprite": self.sprites.get(enemy_type),
            "last_atk_time": time.time(),
            "is_boss": is_boss,
            "sin_anim": 0
        }

        
        self.active_words = {}
        self.generate_word_set(force=True)
        self.typed_buffer = ""
        self.combo_count = 0

    def generate_word_set(self, force=False): 
        # Если мы передаем force=True, то CRIT и HEAL появятся гарантированно
        # (это полезно при старте битвы)
        
        self.active_words = {
            "hit": random.choice(WORDS["hit"]),
            "shield": random.choice(WORDS["shield"]),
            "crit": None,
            "heal": None
        }

        # Шанс для КРИТА (40% или всегда, если force=True)
        if force or random.random() < 0.4: 
            self.active_words["crit"] = random.choice(WORDS["crit"])

        # Шанс для ЛЕЧЕНИЯ (25% или всегда, если force=True)
        if force or random.random() < 0.25:
            self.active_words["heal"] = random.choice(WORDS["heal"])

    def trigger_vfx(self, color, shake=15, flash=150):
        self.screen_flash = flash
        self.flash_color = color
        self.screen_shake = shake

    def handle_word_complete(self, word_type):
        p = self.player
        e = self.enemy
        
        # 1. Сначала определяем базовые параметры
        base_atk = p["atk_bonus"]
        is_crit = (random.random() < p["crit_chance"])
        combo_multiplier = 1 + (self.combo_count * 0.1)
        
        # 2. Добавляем энергию за каждое слово
        self.player["energy"] = min(self.player["max_energy"], self.player["energy"] + 5)
        
        # 3. Логика по типам слов
        if word_type == "hit":
            dmg = int(base_atk * (1.5 if is_crit else 1.0) * combo_multiplier)
            e["hp"] -= dmg
            self.trigger_vfx(C_WHITE, 8, 80)
            self.sounds.play("hit")
            self.vfx_texts.append(FloatingText(200, 200, str(dmg), C_WHITE, is_crit))
            self.vfx_particles.append(ParticleSystem(220, 250, C_WHITE))
            p["total_dmg"] += dmg # Добавляем статистику здесь
            
        elif word_type == "crit":
            dmg = int(base_atk * 3.5 * combo_multiplier)
            e["hp"] -= dmg
            self.trigger_vfx(C_GOLD, 30, 200)
            self.sounds.play("crit")
            self.vfx_texts.append(FloatingText(200, 150, f"SHATTER {dmg}", C_GOLD, True))
            self.vfx_particles.append(ParticleSystem(220, 250, C_GOLD))
            p["total_dmg"] += dmg
            
        elif word_type == "shield":
            sh = 20 + (p["lvl"] * 3)
            p["hp"] = min(p["max_hp"], p["hp"] + sh)
            self.trigger_vfx(C_BLUE, 5, 50)
            self.vfx_texts.append(FloatingText(750, 200, "BLOCK", C_BLUE))
            
        elif word_type == "heal":
            hl = 50 + (p["lvl"] * 10)
            p["hp"] = min(p["max_hp"], p["hp"] + hl)
            self.heal_timer = time.time()
            self.sounds.play("heal")
            self.vfx_particles.append(ParticleSystem(750, 250, C_GREEN))
            self.vfx_texts.append(FloatingText(750, 150, f"+{hl}", C_GREEN))

        # Сброс и генерация нового слова
        self.active_words[word_type] = None
        self.typed_buffer = ""
        self.combo_count += 1
        self.generate_word_set()

    # ОСНОВНОЙ ЦИКЛ ОБНОВЛЕНИЯ
    def update(self, dt):
        # 1. Обновление визуальных эффектов (ВСЕГДА)
        if self.screen_flash > 0: self.screen_flash -= dt * 450
        if self.screen_shake > 0: self.screen_shake -= dt * 35
        
        for ps in self.vfx_particles[:]:
            ps.update(dt) # Здесь вызывается метод частиц, он работает правильно
            if not ps.particles: self.vfx_particles.remove(ps)
            
        for ft in self.vfx_texts[:]:
            ft.update(dt)
            if ft.life <= 0: self.vfx_texts.remove(ft)

        # 2. ЛОГИКА СОСТОЯНИЙ (Только здесь используется self.state)
        if self.state == "BATTLE" and self.enemy:
            # Анимация врага
            self.enemy["sin_anim"] += dt * 4
            
            # Таймер атаки врага (ТОТ САМЫЙ БЛОК С БРОНЕЙ)
            atk_speed = 1.8 if self.enemy["is_boss"] else 2.8
            if time.time() - self.enemy["last_atk_time"] > atk_speed:
                raw_dmg = max(5, self.enemy["atk"] - (self.player["lvl"] * 2))
                # Защита игрока
                final_dmg = max(2, raw_dmg - (self.player.get("armor_lvl", 0) * 5))
                
                self.player["hp"] -= final_dmg
                self.trigger_vfx(C_RED, 25, 150)
                self.sounds.play("hit")
                self.vfx_texts.append(FloatingText(750, 250, f"-{final_dmg}", C_RED))
                self.enemy["last_atk_time"] = time.time()
                self.combo_count = 0
            
            # Проверки смерти
            if self.enemy["hp"] <= 0:
                self.process_victory()
            if self.player["hp"] <= 0:
                self.state = "GAMEOVER"

    def process_victory(self):
        self.sounds.play("death")
        gold_gain = 50 + (self.player["stage"] * 20)
        xp_gain = 35 + (self.player["stage"] * 5)
        
        self.player["gold"] += gold_gain
        self.player["xp"] += xp_gain
        self.player["kills"] += 1
        
        # Повышение уровня
        if self.player["xp"] >= 100:
            self.player["lvl"] += 1
            self.player["xp"] = 0
            self.player["max_hp"] += 25
            self.player["hp"] = self.player["max_hp"]
            self.player["atk_bonus"] += 4
            self.sounds.play("lvlup")
            self.vfx_texts.append(FloatingText(WIDTH//2-50, 100, "LEVEL UP!", C_GOLD, True))
            
        self.save_progress()
        self.state = "VICTORY"

    def set_difficulty(self, name, mult):
        self.player["diff_name"] = name
        self.player["diff_mult"] = mult
        self.state = "NAME_INPUT" # Теперь идем к имени
        self.sounds.play("lvlup")

    def handle_events(self, event):
        mouse_pos = pygame.mouse.get_pos()

        # 1. ОБРАБОТКА МЫШИ (Клики)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == "DIFF_SELECT":
                if 150 < mouse_pos[0] < 350: self.set_difficulty("EASY", 0.7)
                elif 400 < mouse_pos[0] < 600: self.set_difficulty("NORMAL", 1.0)
                elif 650 < mouse_pos[0] < 850: self.set_difficulty("HARD", 1.5)

        # 2. ОБРАБОТКА КЛАВИАТУРЫ (Нажатия)
        elif event.type == pygame.KEYDOWN:
            # Общие клавиши для всех состояний
            if self.state == "MENU":
                if event.key == pygame.K_SPACE:
                    self.state = "DIFF_SELECT"
                    self.sounds.play("click")

            elif self.state == "NAME_INPUT":
                if event.key == pygame.K_RETURN and self.player_input_name.strip():
                    self.player["name"] = self.player_input_name
                    self.state = "CLASS_SELECT"
                    self.sounds.play("click")
                elif event.key == pygame.K_BACKSPACE:
                    self.player_input_name = self.player_input_name[:-1]
                elif event.unicode.isprintable() and len(self.player_input_name) < 15:
                    self.player_input_name += event.unicode

            elif self.state == "CLASS_SELECT":
                keys = {pygame.K_1: "WARRIOR", pygame.K_2: "MAGE", pygame.K_3: "ROGUE"}
                if event.key in keys:
                    self.init_class(keys[event.key])
                    self.start_new_battle()
                    self.state = "BATTLE"
                    self.sounds.play("lvlup")

            elif self.state == "BATTLE":
                if event.key == pygame.K_BACKSPACE:
                    self.typed_buffer = self.typed_buffer[:-1]
                elif event.key == pygame.K_1 and self.player["potions"] > 0:
                    self.player["potions"] -= 1
                    self.player["hp"] = min(self.player["max_hp"], self.player["hp"] + 70)
                    self.sounds.play("heal")
                    self.vfx_particles.append(ParticleSystem(750, 250, C_GREEN))
                
                # ВВОД БУКВ (Теперь гарантированно работает)
                char = event.unicode.lower()
                if char.isalpha() or char in " -'": # Разрешаем буквы, пробел и тире
                    self.typed_buffer += char
                    for w_type, word in self.active_words.items():
                        if word and self.typed_buffer == word:
                            self.handle_word_complete(w_type)
                            break

            elif self.state == "VICTORY":
                if event.key == pygame.K_n:
                    self.player["stage"] += 1
                    self.start_new_battle()
                    self.state = "BATTLE"
                    self.sounds.play("click")
                elif event.key == pygame.K_s:
                    self.state = "SHOP"
                    self.sounds.play("click")

            elif self.state == "SHOP":
                if event.key == pygame.K_ESCAPE:
                    self.state = "VICTORY"
                
                w_price = 150 + (self.player.get("weapon_lvl", 1) * 100)
                a_price = 200 + (self.player.get("armor_lvl", 0) * 150)

                if event.key == pygame.K_1:
                    if self.player["gold"] >= 60:
                        self.player["gold"] -= 60
                        self.player["potions"] += 1
                        self.sounds.play("buy")
                elif event.key == pygame.K_2:
                    if self.player["gold"] >= w_price:
                        self.player["gold"] -= w_price
                        self.player["weapon_lvl"] += 1
                        self.player["atk_bonus"] += 7
                        self.sounds.play("buy")
                elif event.key == pygame.K_3:
                    if self.player["gold"] >= a_price:
                        self.player["gold"] -= a_price
                        self.player["armor_lvl"] += 1
                        self.sounds.play("buy")

            elif self.state == "GAMEOVER":
                if event.key == pygame.K_r: # Вот здесь была твоя ошибка из лога!
                    self.init_player_data()
                    self.player_input_name = "" 
                    self.state = "MENU" 
                    self.sounds.play("click")

    # ОТРИСОВКА
    def render(self):
        # Эффект тряски
        off_x = random.randint(-int(self.screen_shake), int(self.screen_shake)) if self.screen_shake > 0 else 0
        off_y = random.randint(-int(self.screen_shake), int(self.screen_shake)) if self.screen_shake > 0 else 0
        
        temp_surf = pygame.Surface((WIDTH, HEIGHT))
        temp_surf.fill(C_BG)

        if self.state == "MENU": 
            self.draw_menu(temp_surf)
        elif self.state == "NAME_INPUT": 
            self.draw_name_input(temp_surf)
        elif self.state == "CLASS_SELECT": 
            self.draw_class_select(temp_surf)
        
        # --- ИСПРАВЛЕНО ЗДЕСЬ ---
        elif self.state == "DIFF_SELECT": 
            self.draw_diff_select(temp_surf)
        # ------------------------
        
        elif self.state == "BATTLE": 
            self.draw_battle(temp_surf)
        elif self.state == "VICTORY": 
            self.draw_victory(temp_surf)
        elif self.state == "SHOP": 
            self.draw_shop(temp_surf)
        elif self.state == "GAMEOVER": 
            self.draw_gameover(temp_surf)

        # Частицы и текст поверх всего
        for ps in self.vfx_particles: ps.draw(temp_surf)
        for ft in self.vfx_texts: ft.draw(temp_surf)

        # Вспышка
        if self.screen_flash > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT))
            flash_surf.fill(self.flash_color)
            flash_surf.set_alpha(int(self.screen_flash))
            temp_surf.blit(flash_surf, (0,0))

        screen.blit(temp_surf, (off_x, off_y))
        pygame.display.flip()

    def draw_menu(self, surf):
        title = F_BIG.render("KEYSTORM", True, C_GOLD)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        
        pulse = (math.sin(time.time() * 5) + 1) / 2
        col = (200 * pulse + 55, 200 * pulse + 55, 200 * pulse + 55)
        hint = F_MAIN.render("НАЖМИ ПРОБЕЛ ДЛЯ СТАРТА", True, col)
        surf.blit(hint, (WIDTH//2 - hint.get_width()//2, 400))
        
        if self.player["class"]:
            sub = F_UI.render(f"Продолжить: {self.player['name']} ({self.player['class']}) Стадия {self.player['stage']}", True, C_GRAY)
            surf.blit(sub, (WIDTH//2 - sub.get_width()//2, 480))

    def draw_name_input(self, surf):
        surf.fill(C_BLACK)

        title = FONT.render("Введите имя игрока", True, C_WHITE)
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        box = pygame.Rect(WIDTH // 2 - 200, 260, 400, 60)
        pygame.draw.rect(surf, C_BLACK, box, border_radius=12)
        pygame.draw.rect(surf, C_WHITE, box, 2, border_radius=12)

        name_txt = FONT.render(self.player_input_name + "|", True, C_WHITE)
        surf.blit(name_txt, (box.x + 15, box.y + 15))

            
        surf.blit(F_UI.render("ENTER для подтверждения", True, C_GRAY), (WIDTH//2 - 110, 380))
    def load_sprites(self):
        self.sprites = {}
        # Внутренняя функция должна быть с отступом!
        def load_img(name, size):
            path = os.path.join(IMG_FOLDER, name)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, size)
            surf = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(surf, (100, 100, 100), (0, 0, *size), border_radius=10)
            return surf
    def draw_diff_select(self, surf):
        surf.fill(C_BG)
        mouse_pos = pygame.mouse.get_pos()
        
        title = F_BOLD.render("ВЫБЕРИТЕ СЛОЖНОСТЬ", True, C_GOLD)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        # Настройки кнопок: (Название, Позиция X, Цвет, Множитель)
        options = [
            ("ЛЕГКО", 150, C_GREEN, "0.7x Золота"),
            ("НОРМА", 400, C_BLUE, "1.0x Золота"),
            ("ХАРД", 650, C_RED, "1.5x Золота")
        ]

        for name, x, color, desc in options:
            rect = pygame.Rect(x, 250, 200, 150)
            
            # Эффект наведения мыши
            is_hovered = rect.collidepoint(mouse_pos)
            draw_color = color if is_hovered else C_DARK_GRAY
            
            pygame.draw.rect(surf, C_BG_LHT, rect, border_radius=15)
            pygame.draw.rect(surf, draw_color, rect, 3 if is_hovered else 1, border_radius=15)
            
            txt = F_BOLD.render(name, True, draw_color)
            surf.blit(txt, (rect.centerx - txt.get_width()//2, rect.y + 40))
            
            sub = F_UI.render(desc, True, C_GRAY)
            surf.blit(sub, (rect.centerx - sub.get_width()//2, rect.y + 90))
    def draw_class_select(self, surf):
        surf.fill(C_BG)
        mouse_pos = pygame.mouse.get_pos() # Важно!
        
        for i, (c_name, data) in enumerate(CLASSES_DATA.items()):
            # Координаты должны быть такими же, как были раньше
            base_rect = pygame.Rect(80 + (i * 300), 130, 260, 400)
            
            # ПРОВЕРКА НАВЕДЕНИЯ
            is_hovered = base_rect.collidepoint(mouse_pos)
            
            # Если навели - поднимаем карточку вверх на 20 пикселей
            current_y = 130 - 20 if is_hovered else 130
            rect = pygame.Rect(80 + (i * 300), current_y, 260, 400)

            # Рисуем саму карточку
            color = data["color"] if is_hovered else C_DARK_GRAY
            pygame.draw.rect(surf, C_BG_LHT, rect, border_radius=15)
            pygame.draw.rect(surf, color, rect, 3 if is_hovered else 1, border_radius=15)
            
            # Имя и статы
            surf.blit(F_BOLD.render(c_name, True, data["color"]), (rect.x + 20, rect.y + 20))
            stats = [f"Здоровье: {data['hp']}", f"Атака: {data['atk']}", f"Крит: {int(data['crit_c']*100)}%"]
            for j, s in enumerate(stats):
                surf.blit(F_UI.render(s, True, C_WHITE), (rect.x + 20, rect.y + 70 + (j*25)))
            
            # Описание с переносом
            words = data["desc"].split()
            line = ""; cur_y = rect.y + 160
            for w in words:
                if F_DESC.size(line + w)[0] < 220: line += w + " "
                else:
                    surf.blit(F_DESC.render(line, True, C_GRAY), (rect.x + 20, cur_y))
                    line = w + " "; cur_y += 20
            surf.blit(F_DESC.render(line, True, C_GRAY), (rect.x + 20, cur_y))
            
            surf.blit(F_BIG.render(str(i+1), True, C_DARK_GRAY), (rect.x + 180, rect.y + 300))

    def draw_battle(self, surf):
        # Интерфейс статов
        surf.blit(F_UI.render(f"СТАДИЯ: {self.player['stage']}", True, C_GRAY), (30, 20))
        surf.blit(F_UI.render(f"ЗОЛОТО: {self.player['gold']}", True, C_GOLD), (WIDTH - 150, 20))
        
        combo_txt = F_BOLD.render(f"COMBO X{self.combo_count}", True, C_ORANGE)
        surf.blit(combo_txt, (WIDTH//2 - combo_txt.get_width()//2, 20))

        # ВРАГ
        # 1. Полоска ХП и имя
        draw_bar(surf, 115, 180, 250, 22, self.enemy["hp"], self.enemy["max_hp"], C_RED)
        surf.blit(F_MAIN.render(self.enemy["name"], True, C_WHITE), (115, 145))

        # 2. ТЕЛО ВРАГА (с анимацией покачивания)
        bobbing = math.sin(time.time() * 3) * 15
        enemy_rect = pygame.Rect(115, 220 + bobbing, 180, 180)

        if self.enemy.get("sprite"):
            surf.blit(self.enemy["sprite"], enemy_rect)
        else:
            pygame.draw.rect(surf, self.enemy["color"], enemy_rect, border_radius=20)
            pygame.draw.rect(surf, C_WHITE, enemy_rect, 3, border_radius=20)

        # ИГРОК
        px, py = 680, 220
        # Добавим легкое дыхание и игроку для симметрии
        p_bobbing = math.sin(time.time() * 2) * 5 
        
        if self.sprites.get("player"):
            surf.blit(self.sprites["player"], (px, py + p_bobbing))
        else:
            pygame.draw.rect(surf, C_BLUE, (px, py + p_bobbing, 140, 140), border_radius=15)

        draw_bar(surf, 625, 180, 250, 22, self.player["hp"], self.player["max_hp"], C_GREEN)
        surf.blit(F_MAIN.render(self.player["name"], True, C_WHITE), (625, 145))
        surf.blit(F_UI.render(f"LVL {self.player['lvl']} {self.player['class']}", True, C_GRAY), (625, 120))
        
        # ... (дальше ваш код с отрисовкой карточек слов) ...

        # СЛОВА (Дизайн карточек)
        y_pos = 420
        for k, w in self.active_words.items():
            if w:
                is_right = w.startswith(self.typed_buffer) and self.typed_buffer != ""
                pos_x = 100 if k in ["hit", "crit"] else 600
                pos_y = y_pos if k in ["hit", "heal"] else y_pos + 70
                
                card = pygame.Rect(pos_x, pos_y, 300, 55)
                # Стиль карточки
                b_col = C_GOLD if is_right else C_DARK_GRAY
                if k == "crit": b_col = C_PURPLE if not is_right else C_GOLD
                if k == "heal": b_col = C_DARK_GREEN if not is_right else C_GOLD
                
                pygame.draw.rect(surf, C_BG_LHT, card, border_radius=12)
                pygame.draw.rect(surf, b_col, card, 2, border_radius=12)
                
                # Текст слова
                w_rend = F_BOLD.render(w, True, C_WHITE)
                surf.blit(w_rend, (card.x + 20, card.y + 10))
                
                # Метка типа
                label = F_UI.render(k.upper(), True, b_col)
                surf.blit(label, (card.x, card.y - 20))
        
        # Поле ввода
        inp_rect = pygame.Rect(WIDTH//2 - 200, 570, 400, 55)
        pygame.draw.rect(surf, C_BG_LHT, inp_rect, border_radius=15)
        pygame.draw.rect(surf, C_GOLD, inp_rect, 2, border_radius=15)
        txt = F_BOLD.render(f"> {self.typed_buffer}", True, C_WHITE)
        surf.blit(txt, (inp_rect.x + 25, inp_rect.y + 10))
        
        # Инфо о зельях
        p_col = C_RED if self.player["potions"] > 0 else C_DARK_GRAY
        surf.blit(F_UI.render(f"[1] ЗЕЛЬЕ ХП: {self.player['potions']}", True, p_col), (830, 590))

    def draw_victory(self, surf):
        surf.blit(F_BIG.render("ПОБЕДА!", True, C_GOLD), (340, 150))
        
        stats = [
            f"Текущая стадия: {self.player['stage']}",
            f"Золото: {self.player['gold']}",
            f"Опыт: {self.player['xp']} / 100"
        ]
        for i, s in enumerate(stats):
            surf.blit(F_MAIN.render(s, True, C_WHITE), (400, 280 + i*35))
            
        surf.blit(F_BOLD.render("[N] СЛЕДУЮЩИЙ ЭТАП", True, C_GREEN), (340, 450))
        surf.blit(F_BOLD.render("[S] ЗАЙТИ В МАГАЗИН", True, C_BLUE), (340, 500))

    def draw_shop(self, surf):
        surf.blit(F_BIG.render("КУЗНИЦА", True, C_GOLD), (320, 30))
        surf.blit(F_MAIN.render(f"Золото: {self.player['gold']}", True, C_GOLD), (400, 120))
        
        w_price = 150 + (self.player["weapon_lvl"] * 100)
        a_price = 200 + (self.player["armor_lvl"] * 150)

        items = [
            (f"[1] Зелье (60g)", f"У вас: {self.player['potions']} шт."),
            (f"[2] Острить меч ({w_price}g)", f"Ур. {self.player['weapon_lvl']} (+{self.player['atk_bonus']} АТК)"),
            (f"[3] Укрепить броню ({a_price}g)", f"Ур. {self.player['armor_lvl']} (-{self.player['armor_lvl']*5} урона)"),
            (f"[4] Отдых (40g)", "Полное восстановление ХП")
        ]
        
        for i, (name, d) in enumerate(items):
            box = pygame.Rect(150, 180 + i * 100, 700, 85)
            pygame.draw.rect(surf, C_BG_LHT, box, border_radius=12)
            color = C_GOLD if i == 1 or i == 2 else C_BLUE
            pygame.draw.rect(surf, color, box, 1, border_radius=12)
            surf.blit(F_BOLD.render(name, True, C_WHITE), (170, 190 + i*100))
            surf.blit(F_DESC.render(d, True, C_GRAY), (170, 230 + i*100))
            
        surf.blit(F_UI.render("Нажми ESC для выхода", True, C_WHITE), (400, 600))

    def draw_gameover(self, surf):
        surf.blit(F_BIG.render("ГЕРОЙ ПАЛ", True, C_RED), (320, 200))
        surf.blit(F_MAIN.render(f"Вы дошли до {self.player['stage']} стадии", True, C_WHITE), (350, 320))
        surf.blit(F_BOLD.render("НАЖМИ [R] ДЛЯ ВОЗРОЖДЕНИЯ", True, C_ORANGE), (290, 450))

# --- УТИЛИТЫ ---
def draw_bar(surf, x, y, w, h, val, max_val, color):
    ratio = max(0, min(val / max_val, 1))
    pygame.draw.rect(surf, C_BLACK, (x, y, w, h), border_radius=6)
    pygame.draw.rect(surf, color, (x, y, int(w * ratio), h), border_radius=6)
    pygame.draw.rect(surf, C_WHITE, (x, y, w, h), 2, border_radius=6)

# 5. ЗАПУСК
if __name__ == "__main__":
    core = GameCore()
    
    while True:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                core.save_progress()
                pygame.quit()
                sys.exit()
            core.handle_events(event)
            
        core.update(dt)
        core.render()