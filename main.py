import pyxel
import pyxelgrid
from stage_file import Tank, Bullet, Cell, Levels
from stage_file import DIM, ROW, COL, TANK_WIDTH, TANK_LENGTH, CONTROLS
import random


class BattleCity(pyxelgrid.PyxelGrid[int]):
    def __init__(self):
        super().__init__(r = ROW, c = COL, dim = DIM)
        
        
    def init(self):
        # Initialize the game state and load resources
        self.level = Levels()
        self.initial = self.level.list_of_levels
        self.stage_idx = 0
        self.gamestate = self.initial[self.stage_idx]
        

        # Player and enemy initial settings
        self.player_lives = 2
        self.movement = 1
        self.enemymovement = 2
        
        # Initialize cells and positions
        self.Cell: list[Cell]=self.gamestate.cells
        self.defined_positions = {(cell.i,  cell.j) for cell in self.Cell}

        # Initialize tanks
        self.tanks: list[Tank]=self.gamestate.player_tank
        self.tanks_appended = 0
        self.standard_tanks = []
        self.special_tanks = []
        self.first_lvl_enemies=len(self.gamestate.enemy_tanks)
        for tank in self.gamestate.player_tank:
            if tank.type == "enemy":
                self.first_lvl_enemies += 1

        # Initialize all possible positions
        self.all_positions = {(x,  y) for x in range(COL) for y in range(ROW)}
        self.no_state_positions = self.all_positions - self.defined_positions

        # Powerup settings
        self.spawn_powerup=True
        self.has_powerup=False
        self.powerup_cooldown=1000

        # Categorize tanks into standard and special tanks randomly
        for tank in self.tanks:
            if tank.type == "enemy":
                number=random.randint(1, 2)
                if number == 1:
                    self.standard_tanks.append(tank)
                else:
                    self.special_tanks.append(tank)

        #Bullet Settings
        self.bullets: list[Bullet]=[]
        self.bulletspeed = 3
        self.bullet_speed_y = [-1*self.bulletspeed, 1*self.bulletspeed, 0, 0]
        self.bullet_speed_x=[0, 0, -1*self.bulletspeed, 1*self.bulletspeed]
        self.black_screen=[Cell for Cell in self.Cell if Cell.is_blank]
        
        # Cooldown settings for shooting
        self.cooldown=20
        self.recent_button: int = 0 
        self.recent_button_timer: int = 0
        self.bullet_per_every_frame=10
        self.bullet_radius=2

        # Use of cheat code indicator
        self.can_cheat = True

        # Cooldown settings for shooting
        self.explosion:list[tuple[float, float]]=[] #(i, j)
        self.tank_explosion:list[tuple[float, float]]=[] #(x, y)
        self.explosioncooldown=20

        # Direction and movement settings
        self.dir = ["north", "south", "west", "east"]
        self.vy = [-1, 1, 0, 0]
        self.vx = [0, 0, -1, 1]

        # Game completion flag
        self.complete_game = False

    # Load pyxel resources and settings
        pyxel.load("graphics.pyxres")
        pyxel.playm(0, loop=True)
        pyxel.mouse(visible=True)


    def init_state(self):
        return Levels()


    def reset_game(self): 
        # Initialize the game state and level settings
        self.level = self.init_state()
        self.initial = self.level.list_of_levels
        self.stage_idx = 0
        self.gamestate = self.initial[self.stage_idx]

        # Set initial game variables
        self.tanks_appended = 0
        self.tanks = self.gamestate.player_tank
        self.Cell = self.gamestate.cells
        self.bullets = []
        self.player_lives = 2

        # Initialize enemy tank counters
        self.first_lvl_enemies = len(self.gamestate.enemy_tanks)
        self.standard_tanks = []
        self.special_tanks = []
        
        # Play background music
        pyxel.playm(0, loop=True)

        # Classify enemy tanks into standard and special categories
        for tank in self.tanks:
            if tank.type == "enemy":
                number = random.randint(1, 2)
                if number == 1:
                    self.standard_tanks.append(tank)
                else:
                    self.special_tanks.append(tank)

        # Set positions for gameplay elements
        self.all_positions = {(x, y) for x in range(COL) for y in range(ROW)}
        self.defined_positions = {(cell.i, cell.j) for cell in self.Cell}
        self.no_state_positions = self.all_positions - self.defined_positions

        # Initialize powerup and gameplay flags
        self.spawn_powerup = True
        self.has_powerup = False
        self.speedup = False
        self.nodelay = False
        self.can_cheat = True
        self.complete_game = False


    def set_stage(self, n: int):
        # Set the stage index and initialize the game state for the new stage
        self.stage_idx = n
        self.gamestate = self.initial[self.stage_idx]

        # Reset game variables for the new stage
        self.tanks_appended = 0
        self.bullets = []
        self.tanks_killed_num = 0

        # Calculate the number of enemy tanks in the first level
        self.first_lvl_enemies = sum(1 for tank in self.gamestate.player_tank if tank.type == "enemy") + len(self.gamestate.enemy_tanks)

        # Set the player's tanks and game cells
        self.tanks = self.gamestate.player_tank
        self.Cell = self.gamestate.cells

        # Initialize lists for different types of tanks
        self.standard_tanks = []
        self.special_tanks = []

        # Classify enemy tanks into standard and special categories
        for tank in self.tanks:
            if tank.type == "enemy":
                number = random.randint(1, 2)
                if number == 1:
                    self.standard_tanks.append(tank)
                else:
                    self.special_tanks.append(tank)

        # Set positions for gameplay elements
        self.all_positions = {(x, y) for x in range(COL) for y in range(ROW)}
        self.defined_positions = {(cell.i, cell.j) for cell in self.Cell}
        self.no_state_positions = self.all_positions - self.defined_positions

        # Initialize powerup flag and game completion flag
        self.spawn_powerup = True
        self.complete_game = False


    def tank_goes_thru_cell(self, tank: Tank):
        cells = self.Cell

        # Iterate over each cell to check for collision
        for cell in cells:
            # Skip cells that are not collidable (forest or powerup)
            if cell.type is not None and cell.type != "forest" and cell.type != "powerup":
                i, j = cell.i, cell.j
                
                # Calculate the cell's boundaries in terms of game dimensions
                start_h, end_h = (i * self.dim), ((i + 1) * self.dim)
                start_w, end_w = (j * self.dim), ((j + 1) * self.dim)
                
                # Check for collision based on the tank's direction
                if tank.dir in ["north", "south"]:
                    # For north or south direction, check if tank intersects the cell's boundaries
                    if is_intersecting((start_w, end_w), (tank.x, tank.x + TANK_WIDTH - 1)) and \
                    is_intersecting((start_h, end_h), (tank.y, tank.y + TANK_LENGTH - 1)):
                        return True, (i, j)
                    
                elif tank.dir in ["west", "east"]:
                    # For east or west direction, check if tank intersects the cell's boundaries
                    if is_intersecting((start_w, end_w), (tank.x, tank.x + TANK_LENGTH - 1)) and \
                    is_intersecting((start_h, end_h), (tank.y, tank.y + TANK_WIDTH - 1)):
                        return True, (i, j)
        
        # Return False if no collision is detected
        return False


    def get_powerup(self, tank: Tank):
        # Retrieve the list of game cells
        cells = self.Cell

        # Check if the tank is a player tank
        if tank.type == "player":
            # Iterate over each cell to check for powerup collision
            for cell in cells:
                if cell.type == "powerup":
                    i, j = cell.i, cell.j
                    
                    # Calculate the cell's boundaries in terms of game dimensions
                    start_h, end_h = ((i) * self.dim), ((i + 1) * self.dim)
                    start_w, end_w = ((j) * self.dim), ((j + 1) * self.dim)

                    # Check for collision based on the tank's direction
                    if tank.dir in ["north", "south"]:
                        if is_intersecting((start_w, end_w), ((tank.x), (tank.x + TANK_WIDTH - 1))) \
                                and is_intersecting((start_h, end_h), ((tank.y), (tank.y + TANK_LENGTH - 1))):
                            return True, (i, j)
                    elif tank.dir in ["east", "west"]:
                        if is_intersecting((start_w, end_w), ((tank.x), (tank.x + TANK_LENGTH - 1))) \
                                and is_intersecting((start_h, end_h), ((tank.y), (tank.y + TANK_WIDTH - 1))):
                            return True, (i, j)

            # Return False if no powerup collision is detected
            return False
        

    def tank_inbounds(self, tank: Tank):
        #Check if the tank is within game bounds and not colliding with cells
        return not ((tank.x >= self.width - 16 or tank.y >= self.height - 16 or tank.x <= 0 or tank.y <= 0) or self.tank_goes_thru_cell(tank))


    def move_tank(self, direction: str, tank: Tank):
        # Update the tank's direction and velocity based on input direction
        vy = self.vy
        vx = self.vx
        tank.dir = direction
        tank.vy = vy[self.dir.index(tank.dir)]
        tank.vx = vx[self.dir.index(tank.dir)]

        # Move the tank based on its type
        if tank.type == "player":
            for _ in range(self.movement):
                tank.y += tank.vy
                tank.x += tank.vx
        elif tank.type == "enemy":
            for _ in range(self.enemymovement):
                tank.y += tank.vy
                tank.x += tank.vx

        # Revert movement if tank goes out of bounds
        if not self.tank_inbounds(tank):
            if tank.type == "player":
                tank.y -= tank.vy * self.movement
                tank.x -= tank.vx * self.movement
            elif tank.type == "enemy":
                tank.y -= tank.vy * self.enemymovement
            tank.x -= tank.vx * self.enemymovement



    def bullet_collision(self, bullet: Bullet):
        cells = self.Cell
        vx, vy = bullet.vx, bullet.vy

        # Iterate over each cell to check for bullet collision
        for material in cells:
            if  material.type not in ["southeast_mirror", "northeast_mirror", "water", "forest", "powerup"] and material.type is not None:
                i, j=material.i, material.j
                
                start_h, end_h=((i)*self.dim), ((i+1)*self.dim)
                start_w, end_w=((j)*self.dim), ((j+1)*self.dim)
                
                if start_w<=bullet.x<=end_w and start_h<=bullet.y<=end_h:
                    # Handle explosions based on bullet's direction
                    if vx < 0:
                        self.explosion.append((i, j+1))
                    elif vx > 0:
                        self.explosion.append((i, j-1))
                    elif vy < 0:
                        self.explosion.append((i+1, j))
                    elif vy > 0:
                        self.explosion.append((i-1, j))

                    if bullet.shooter=="player":
                        pyxel.play(3, 1)

                    return True, (i, j)
        return False


    def bullet_hits_bullet(self, bullet: Bullet):
        for bullets in self.bullets:
            if bullets != bullet:
                if is_intersecting((bullet.x-self.bullet_radius+self.bulletspeed, bullet.x+self.bullet_radius+self.bulletspeed),
                                (bullets.x-self.bullet_radius+self.bulletspeed, bullets.x+self.bullet_radius+self.bulletspeed)) \
                                and is_intersecting((bullet.y-self.bullet_radius+self.bulletspeed, bullet.y+self.bullet_radius+self.bulletspeed),
                                (bullets.y-self.bullet_radius+self.bulletspeed, bullets.y+self.bullet_radius+self.bulletspeed)):
                    
                    x1, y1=bullets.x, bullets.y
                    x2, y2=bullet.x, bullet.y
                    self.tank_explosion.append((x1, y1))
                    self.tank_explosion.append((x2, y2))

                    # Play sound and remove bullets from the list
                    pyxel.play(3, 1)
                    self.bullets.remove(bullet)
                    self.bullets.remove(bullets)


    def mirror_bounds(self, x1: int, x2: int, y1: int, y2: float, x: float, y: float):
         # Determine the minimum and maximum bounds for x and y
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        return x_min <= x <= x_max and y_min <= y <= y_max
                    

    def bullet_hits_mirror(self, bullet: Bullet):
        cells = self.Cell
        vx, vy = bullet.vx, bullet.vy
        direction_index =- 1

        # Determine bullet's current direction index
        if vx != 0:
            direction_index=self.bullet_speed_x.index(vx)
        if vy != 0:
            direction_index=self.bullet_speed_y.index(vy)
        bullet_direction = self.dir[direction_index]
        
        # Check for collision with each cell
        for material in cells:
            if material.type == "northeast_mirror":
                change_of_dir = {"north":"east", "east":"north", "south":"west", "west":"south"}
                new_direction = change_of_dir[bullet_direction]
                direction_index = self.dir.index(new_direction)
                i, j = material.i, material.j
                start_h, end_h = ((i)*self.dim), ((i+1)*self.dim)
                start_w, end_w = ((j)*self.dim), ((j+1)*self.dim)
                if self.mirror_bounds(start_w, end_w, start_h, end_h, bullet.x, bullet.y):
                    bullet.shooter="friendly fire"
                    bullet.vy = self.bullet_speed_y[direction_index]
                    bullet.vx = self.bullet_speed_x[direction_index]

            elif material.type == "southeast_mirror":
                change_of_dir = {"east":"south", "south":"east", "west":"north", "north":"west"}
                new_direction=change_of_dir[bullet_direction]
                direction_index = self.dir.index(new_direction)
                i, j=material.i, material.j
                start_h, end_h = ((i)*self.dim), ((i+1)*self.dim)
                start_w, end_w = ((j)*self.dim), ((j+1)*self.dim)
                if self.mirror_bounds(start_w, end_w, start_h, end_h, bullet.x, bullet.y):
                    bullet.shooter="friendly fire"
                    bullet.vy = self.bullet_speed_y[direction_index]
                    bullet.vx = self.bullet_speed_x[direction_index]


    def tank_hits_bullet(self, bullet: Bullet):
        tanks = self.tanks
        shooter = bullet.shooter

        for tank in tanks:
            start_h, end_h=tank.y, tank.y+TANK_LENGTH - 1
            start_w, end_w=tank.x, tank.x+TANK_WIDTH - 1
            
            #Checks if bullet hits the tank
            if start_w <= bullet.x <= end_w and start_h <= bullet.y <= end_h:
                if shooter=="player" and tank.type=="enemy" and tank.is_alive:
                    tank.is_alive = False
                    self.gamestate.enemy_tanks_num-=1
                    self.tank_explosion.append((tank.x, tank.y))
                    pyxel.play(3, 1)
                    if self.bullets and bullet in self.bullets:
                        self.bullets.remove(bullet)

                elif (shooter=="enemy" or shooter=="friendly fire") and tank.type=="player":
                    if tank.is_alive:
                        self.powerup_cooldown=0
                        self.player_lives-=1
                    tank.is_alive=False
                    
                    if self.bullets and bullet in self.bullets:
                        self.bullets.remove(bullet)


    def shoot_bullets(self, tank:Tank)->None:
            x = tank.x+8
            y = tank.y+8

            dir_idx = self.dir.index(tank.dir)
            bullet_vx = self.bullet_speed_x[dir_idx]
            bullet_vy = self.bullet_speed_y[dir_idx]

            #Adjusts the bullet position based on its direction
            if bullet_vx > 0:
                x += 8
            elif bullet_vx < 0:
                x -= 8
            if bullet_vy > 0:
                y += 8
            elif bullet_vy < 0:
                y -= 8

            #Creates and adds bullet based on tank type
            if not any(bullet.shooter == "player" for bullet in self.bullets) and tank.type == "player":
                bullet=Bullet(x, y, bullet_vx, bullet_vy, tank.type)
                if bullet.shooter=="player":
                    pyxel.play(3, 0)
                self.bullets.append(bullet)
            
            elif tank.type=="enemy":
                bullet=Bullet(x, y, bullet_vx, bullet_vy, tank.type)
                self.bullets.append(bullet)

    def button_cooldown(self):
        #Resets the button press cooldown timer if it reaches zero
        if self.recent_button_timer == 0:
            self.recent_button_timer = self.cooldown


    def update(self):
        if not self.gamestate.is_game_over:
            #Spawns enemy tanks periodically
            if pyxel.frame_count != 0 and pyxel.frame_count % 150 == 0 and self.tanks_appended < len(self.gamestate.enemy_tanks):
                number=random.randint(1,2)
                if number==1:
                    self.standard_tanks.append(self.gamestate.enemy_tanks[self.tanks_appended])
                else:
                    self.special_tanks.append(self.gamestate.enemy_tanks[self.tanks_appended])
                self.gamestate.player_tank.append(self.gamestate.enemy_tanks[self.tanks_appended])
                self.tanks_appended+=1

            #Handles player tank actions
            for tank in self.tanks:
                if tank.type=="player" and tank.is_alive:
                    if self.recent_button_timer > 0:
                        self.recent_button_timer -= 1

                    #WASD Keys and Spacebar also have cooldowns to avoid repetitive user inputs
                    if pyxel.btnp(pyxel.KEY_W, hold = 1, repeat = 1):
                        if self.recent_button == pyxel.KEY_W or self.recent_button_timer == 0:
                            self.recent_button = pyxel.KEY_W
                            self.move_tank(CONTROLS[pyxel.KEY_W],tank)
                        if self.recent_button_timer == 0:
                            self.recent_button_timer = self.cooldown

                    elif pyxel.btnp(pyxel.KEY_A, hold = 1, repeat = 1):
                        if self.recent_button == pyxel.KEY_A or self.recent_button_timer == 0:
                            self.recent_button = pyxel.KEY_A
                            self.move_tank(CONTROLS[pyxel.KEY_A],tank)
                        if self.recent_button_timer == 0:
                            self.recent_button_timer = self.cooldown

                    elif pyxel.btnp(pyxel.KEY_S, hold = 1, repeat = 1):
                        if self.recent_button == pyxel.KEY_S or self.recent_button_timer == 0:
                            self.recent_button = pyxel.KEY_S
                            self.move_tank(CONTROLS[pyxel.KEY_S],tank)
                        if self.recent_button_timer == 0:
                            self.recent_button_timer = self.cooldown

                    elif pyxel.btnp(pyxel.KEY_D,hold=1,repeat=1):
                        if self.recent_button == pyxel.KEY_D or self.recent_button_timer == 0:
                            self.recent_button = pyxel.KEY_D
                            self.move_tank(CONTROLS[pyxel.KEY_D],tank)
                        if self.recent_button_timer == 0:
                            self.recent_button_timer = self.cooldown
                    
                    if pyxel.btnp(pyxel.KEY_SPACE,hold=1,repeat=self.bullet_per_every_frame):
                        self.shoot_bullets(tank)

                '''
                Implementation of Enemy Tanks' AI:

                    Standard tanks can change facing, move towards where they are facing, or shoot a bullet every 20 frames.
                    Special tanks can do the same actions, but they do one action for every 10 frames only. They also move faster than standard tanks.

                    All possible actions have a 33% chance of being done by an enemy tank. 
                '''
                frame_num = 20
                quickness = 2
                if tank.type == "enemy" and tank.is_alive:
                    if tank in self.standard_tanks:
                        frame_num = 20
                        quickness = 2
                    elif tank in self.special_tanks:
                        frame_num = 10
                        quickness = 4

                    choices = ["facing", "move","fire"]
                    chances = [0.33, 0.33,0.33]
                    direction = self.dir
                    if pyxel.frame_count % frame_num==0:
                        result = random.choices(choices, chances, k = 1)[0]
                        if result==choices[0]:
                            index=random.randint(0,3)
                            tank.dir=direction[index]
                        if result==choices[1]:
                            for _ in range(quickness):
                                self.move_tank(tank.dir,tank)
                        if result==choices[2]:
                            self.shoot_bullets(tank)

                #Press R to revive tank when it died and still has lives remaining
                if tank.type=="player" and not tank.is_alive and self.player_lives != 0:
                    if pyxel.btnp(pyxel.KEY_R):
                        tank.is_alive=True

                #Cooldown for bullet explosions
                if self.explosion:
                    self.explosioncooldown-=1
                    if self.explosioncooldown<=0:
                        self.explosion=[]
                        self.explosioncooldown=20

                #Powerup flag for an extra life
                is_powerup=self.get_powerup(tank)
                if is_powerup and tank.type=="player":
                    x,y = is_powerup[1]
                    self.Cell.remove(Cell(x,y,self.dim,self.dim,"powerup",False))
                    self.has_powerup=True


            for bullet in self.bullets:
                self.bullet_hits_bullet(bullet)
                self.tank_hits_bullet(bullet)
                self.bullet_hits_mirror(bullet)
                if not self.bullet_collision(bullet):
                    bullet.x+=bullet.vx
                    bullet.y+=bullet.vy
                elif self.bullet_collision(bullet):
                    result=self.bullet_collision(bullet)
                    assert  isinstance (result,tuple)
                    coordinate=result[1]
                    for cell in self.Cell:
                        if cell.i==coordinate[0] and cell.j==coordinate[1] and cell.type=="brick":
                            cell.type="cracked_brick"
                        elif cell.i==coordinate[0] and cell.j==coordinate[1] and cell.type=="cracked_brick":
                            self.no_state_positions.add((cell.i,cell.j))
                            cell.type=None
                        elif cell.i==coordinate[0] and cell.j==coordinate[1] and cell.type=="home":
                            cell.type=None
                            self.gamestate.is_game_over=True
                    if self.bullets:
                        self.bullets.remove(bullet)
            
            #When at least half of the enemy tanks in a level are killed, a powerup will appear randomly in any empty cell
            if self.gamestate.enemy_tanks_num==(self.first_lvl_enemies // 2):
                if self.spawn_powerup:
                    x, y = random.choice(list(self.no_state_positions))
                    self.Cell.append(Cell(x, y, self.dim, self.dim, "powerup", False))
                    self.spawn_powerup=False
                    
            #Handles powerup duration and cooldown
            if self.has_powerup and self.powerup_cooldown > 0:
                self.player_lives+=1
                self.powerup_cooldown=0
                self.powerup_cooldown-=1

            if self.powerup_cooldown==0:
                self.has_powerup = False
                self.powerup_cooldown = 500
            
            if self.gamestate.enemy_tanks_num==0:
                self.gamestate.is_winner=True
                if self.stage_idx+1<len(self.initial):
                    self.set_stage(self.stage_idx+1)

            #Checks for win condition
            if all(stage.is_winner == True for stage in self.initial):
                self.gamestate.is_game_over=True
                self.complete_game=True

            #Checks for game over condition
            if self.player_lives==0:
                self.gamestate.is_game_over=True

            #Press 0 to reset game while in-game and player tank is alive
            if pyxel.btnp(pyxel.KEY_0):
                self.reset_game()

            #Handles cheat code - Left Shift + Q for an extra life
            if pyxel.btn(pyxel.KEY_LSHIFT) and pyxel.btn(pyxel.KEY_Q):
                if self.can_cheat:
                    self.player_lives += 1
                    self.can_cheat = False  

        #Game over when no more lives are left or when the home cell is shot, whichever happpens first
        #Press T to play the game again
        if self.gamestate.is_game_over:
            if pyxel.btnp(pyxel.KEY_T):
                self.reset_game()

        
    def draw_cell(self,  i: int,  j: int,  x: int,  y: int) -> None:
        for cell in self.Cell:
            if cell.i==i and cell.j==j and cell.type=="stone":
                pyxel.blt(x, y, 1, 0, 0, self.dim, self.dim)
            if cell.i == i and cell.j == j and cell.type == "brick":
                pyxel.blt(x, y, 1, 0, 48, self.dim, self.dim)
            if cell.i == i and cell.j == j and cell.type == "cracked_brick":
                pyxel.blt(x, y, 1, 16, 48, self.dim, self.dim)
            if cell.i == i and cell.j == j and cell.type == "northeast_mirror":
                pyxel.blt(x, y, 1, 0, 64, self.dim, self.dim, 0)
            if cell.i == i and cell.j == j and cell.type == "southeast_mirror":
                pyxel.blt(x, y, 1, 0, 80, self.dim, self.dim, 0)
            if cell.i == i and cell.j == j and cell.type == "water":
                pyxel.blt(x, y, 1, 16, 64, self.dim, self.dim)
            if cell.i == i and cell.j == j and cell.type == "home":
                pyxel.blt(x, y, 1, 48, 32, self.dim, self.dim)
            if cell.i == i and cell.j == j and cell.type == "forest":
                pyxel.blt(x, y, 1, 16, 80, self.dim, self.dim, 0)
            if cell.i == i and cell.j == j and cell.type == "powerup":
                pyxel.blt(x, y, 1, 16, 0, self.dim, self.dim, 0)
            if cell.i == i and cell.j == j and cell in self.black_screen:
                pyxel.rect(x, y, 16, 16, 1)

        if (i, j) in self.explosion:
            pyxel.blt(x, y, 0, 16, 32, self.dim, self.dim)

        #Lives, Enemies, Powerup, and Cheat Indicators
        pyxel.text(16, 10, f"Lives left: {self.player_lives}", 7)
        pyxel.text(105, 10, f"Enemies to kill: {self.gamestate.enemy_tanks_num}", 7)
        if self.has_powerup:
            pyxel.text(200, 10, f"Powerup: Extra life!<3", 7)
        if not self.can_cheat:
            pyxel.text(70, 310, f"Cheat Code has been used for extra life!:<", 7)


    def pre_draw_grid(self) -> None:
        pyxel.cls(0)

        #Uses the sprites from graphics.pyxres to display images for cells, tanks, and explosion effects
        for (x, y) in self.tank_explosion:
            pyxel.blt(x, y, 0, 16, 80, self.dim, self.dim)

        for tank in self.tanks:
            if tank.is_alive:
                if tank.type == "player":
                    if tank.dir == "north":
                        pyxel.blt(tank.x, tank.y, 0, 0, 0, TANK_WIDTH, TANK_LENGTH, colkey=0)
                    elif tank.dir == "south":
                        pyxel.blt(tank.x, tank.y, 0, 16, 0, TANK_WIDTH, TANK_LENGTH, colkey=0)
                    elif tank.dir == "east":
                        pyxel.blt(tank.x, tank.y, 0, 0, 16, TANK_WIDTH, TANK_LENGTH, colkey=0)
                    elif tank.dir == "west":
                        pyxel.blt(tank.x, tank.y, 0, 16, 16, TANK_WIDTH, TANK_LENGTH, colkey=0)
                elif tank.type == "enemy":
                    if tank in self.standard_tanks:
                        if tank.dir == "north":
                            pyxel.blt(tank.x, tank.y, 1, 0, 16, TANK_WIDTH, TANK_LENGTH, colkey=0)
                        elif tank.dir == "south":
                            pyxel.blt(tank.x, tank.y, 1, 16, 16, TANK_WIDTH, TANK_LENGTH, colkey=0)
                        elif tank.dir == "east":
                            pyxel.blt(tank.x, tank.y, 1, 0, 32, TANK_WIDTH, TANK_LENGTH, colkey=0)
                        elif tank.dir == "west":
                            pyxel.blt(tank.x, tank.y, 1, 16, 32, TANK_WIDTH, TANK_LENGTH, colkey=0)
                    elif tank in self.special_tanks:
                        if tank.dir == "north":
                            pyxel.blt(tank.x , tank.y, 1, 32, 48, TANK_WIDTH, TANK_LENGTH, colkey=0)
                        elif tank.dir == "south":
                            pyxel.blt(tank.x, tank.y, 1, 48, 49, TANK_WIDTH, TANK_LENGTH, colkey=0)
                        elif tank.dir == "east":
                            pyxel.blt(tank.x, tank.y, 1, 33, 64, TANK_WIDTH, TANK_LENGTH, colkey=0)
                        elif tank.dir == "west":
                            pyxel.blt(tank.x, tank.y, 1, 48, 64, TANK_WIDTH, TANK_LENGTH, colkey=0)
                            
            elif tank.type == "player" and not tank.is_alive:
                pyxel.blt(tank.x, tank.y, 0, 0, 32, TANK_WIDTH, TANK_LENGTH, colkey=0)
                
        #Uses circles as representations for bullets 
        bullets = self.bullets
        for bullet in bullets:
            if bullet.shooter == "player" or bullet.shooter == "friendly fire":
                pyxel.circ(bullet.x, bullet.y, self.bullet_radius, 7)
            elif bullet.shooter == "enemy":
                pyxel.circ(bullet.x, bullet.y, self.bullet_radius, 8)

    #Stops all game elements when you win or lose the game (game over state). 
    #Displays appropriate message as indicator of the game's outcome (you win or lose the game)
    def post_draw_grid(self) -> None:
        if self.gamestate.is_game_over and not self.complete_game:
            pyxel.blt(130, 160, 1, 32, 3, 63, 13)
        if self.complete_game and self.gamestate.is_game_over:
            pyxel.blt(130, 160, 1, 32, 82, 63, 95)

#For determining intersecting objects in the game
def is_intersecting(x, y):
   return not((x[0] > y[1]) or (x[1] < y[0]))


battle_city = BattleCity()
#Starts the game itself
battle_city.run(title = "Battle City", fps = 60)