import pygame
import sys
import random
import time
# import smbus                          #for using I2C Interface of IMU
import math

pygame.init()
display_width = 800
display_height = 600
rocket_width = 150
red = (255, 0, 0)
green = (0, 255, 0)
dark_red = (200, 0, 0)
dark_green = (0, 200, 0)
blue = (0,0,255)
black = (0, 0, 0)
white = (255, 255, 255)
yellow = (255,255,0)
colors = white,yellow,blue,red
gameDisplay = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('space rocker')
clock = pygame.time.Clock()
rimg = pygame.image.load('rocket.png')
center = display_width/2, display_height/2

pygame.mixer.music.load("war.wav")
crash_sound = pygame.mixer.Sound("crash.ogg")
intro_music = pygame.mixer.Sound("space.wav")
fire = pygame.mixer.Sound("fire.wav")
# bus = smbus.SMBus(1)  # bus = smbus.SMBus(0) for Revision 1
# address = 0x68  # via i2cdetect
# Register
# power_mgmt_1 = 0x6b
# power_mgmt_2 = 0x6c
# Now wake the 6050 up as it starts in sleep mode
# bus.write_byte_data(address, power_mgmt_1, 0)                       #Uncomment for controlling over accelerometer

def read_byte(reg):
    return bus.read_byte_data(address, reg)


def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg + 1)
    value = (h << 8) + l
    return value


def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val


def dist(a, b):
    return math.sqrt((a * a) + (b * b))


def get_x_rotation(x, y, z):
    radians = math.atan2(y, dist(x, z))
    return math.degrees(radians)


def get_y_rotation(x, y, z):
    radians = math.atan2(x, dist(y, z))
    return -math.degrees(radians)


def ComplementaryFilter(accData, gyrData, filtered_pitch, filtered_roll):
    dt = 0.01                                                         # 10 ms sample rate!
    GYROSCOPE_SENSITIVITY = 131.0
    ACCELEROMETER_SENSITIVITY = 16384.0
    # Integrate the gyroscope data -> int(angularSpeed) = angle
    filtered_pitch += float(gyrData[0]) / GYROSCOPE_SENSITIVITY * dt  # Angle around the X-axis
    filtered_roll -= float(gyrData[1]) / GYROSCOPE_SENSITIVITY * dt   # Angle around the Y-axis

    # Compensate for drift with accelerometer data if !bullshit
    # Sensitivity = -2 to 2 G at 16Bit -> 2G = 32768 && 0.5G = 8192
    forceMagnitudeApprox = abs(accData[0]) + abs(accData[1]) + abs(accData[2])
    if forceMagnitudeApprox > 16384 and forceMagnitudeApprox < 32768:
        # Turning around the X axis results in a vector on the Y-axis
        pitchAcc = math.atan2(float(accData[1]), float(accData[2])*180 / math.pi)
        filtered_pitch = filtered_pitch * 0.98 + pitchAcc * 0.02

        # Turning around the Y axis results in a vector on the X-axis
        rollAcc = math.atan2(float(accData[0]), float(accData[2])*180 / math.pi)
        filtered_roll = filtered_roll * 0.98 + rollAcc * 0.02
    return [filtered_pitch,filtered_roll]


def getInput():
    time.sleep(0.5)
    gy_x = read_word_2c(0x43)
    gy_y = read_word_2c(0x45)
    gy_z = read_word_2c(0x47)

    # Full scale range +/- 250 degree/C as per sensitivity scale factor
    Gx = gy_x / 131.0
    Gy = gy_y / 131.0
    Gz = gy_z / 131.0

    gyrData = gy_x,gy_y,gy_z
    ac_x = read_word_2c(0x3b)
    ac_y = read_word_2c(0x3d)
    ac_z = read_word_2c(0x3f)

    # Full scale range +/- 2g ([-32768, +32767]) as per sensitivity scale factor
    Ax = ac_x / 16384.0
    Ay = ac_y / 16384.0
    Az = ac_z / 16384.0
    accData = ac_x,ac_y,ac_z
    pitch = get_x_rotation(Ax, Ay, Az)
    roll = get_y_rotation(Ax, Ay, Az)

    #x = ComplementaryFilter(accData, gyrData, pitch, roll)
    return [pitch, roll]


def things(thingx, thingy, thingw, thingh, color):
    pygame.draw.rect(gameDisplay, color, [thingx, thingy, thingw, thingh])


def rocket(x, y):
    gameDisplay.blit(rimg, (x, y))


def handlefile(dc):
    f1 = open("myfile.txt", "w+")
    f1.write(str(dc))
    f1.close()


def crash(dc,level):
    pygame.mixer.music.stop()
    pygame.mixer.Sound.play(crash_sound)
    font = pygame.font.Font(None, 150)
    crashText = font.render("CRASHED", 1, red)
    message_display(crashText)
    time.sleep(2)
    highscore(dc)
    dc = 0
    level=0
    # restarttext = font.render("GAME RESTARTED", 1, green)
    # gameDisplay.blit(restarttext, (0, 0))
    # time.sleep(2)
    game_loop(dc,level,3)


def message_display(msg):
    textpos = msg.get_rect(
        centerx=display_width / 2,
        centery=display_height / 2
    )
    gameDisplay.blit(msg, textpos)
    pygame.display.flip()


def button(msg,x,y,w,h,inactive,active,action):
    mouse =pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x+w >mouse[0]>x and y+h> mouse[1] >y:
        pygame.draw.rect(gameDisplay,active,(x,y,w,h))
        if click[0] == 1 :
            if action=="play":
                pygame.mixer.Sound.stop(intro_music)
                start()
                game_loop(0,0,3)
            elif action=="quit":
                quit()
    else:
        pygame.draw.rect(gameDisplay, inactive, (x, y, w, h))
    font = pygame.font.Font('freesansbold.ttf', 20)
    buttontext = font.render(msg, 1, black)
    textpos = buttontext.get_rect(centerx=(x+w/2),centery=(y+h/2))
    gameDisplay.blit(buttontext, textpos)


def game_intro():
    pygame.mixer.Sound.play(intro_music)
    intro = True
    while intro:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        bg = pygame.image.load("1.jpg")
        gameDisplay.blit(bg, (0, 0))
        font = pygame.font.Font('freesansbold.ttf', 90)
        introtext1 = font.render("SPACE", 1, yellow)
        textpos1 = introtext1.get_rect(topleft=(3 * display_width / 10,display_height / 3))
        gameDisplay.blit(introtext1, textpos1)
        introtext2 = font.render("ROCKER", 1, yellow)
        textpos2 = introtext2.get_rect(topleft=(display_width / 4,display_height / 2))
        gameDisplay.blit(introtext2, textpos2)
        button("START",150,display_height-80,100,50,dark_green,green,"play")
        button("QUIT", 550, display_height-80, 100, 50, dark_red, red,"quit")

        pygame.display.update()
        clock.tick(15)

def start():
    gameDisplay.fill(black)
    font = pygame.font.Font(None, 100)
    startText = font.render("HERE YOU GO!!", 1, green)
    message_display(startText)
    time.sleep(2)
    handlefile(0)


def things_doged(count):
    font = pygame.font.SysFont(None, 25)
    text = font.render("Dogded: " + str(count), 1, white)
    gameDisplay.blit(text, (0, 0))


def highscore(dc):
    f = open("myfile.txt", "r")
    score = []
    for val in f.read().split():
        score.append(int(val))
    f.close()
    if dc >= score[0]:
        handlefile(dc)
        font = pygame.font.SysFont(None, 25)
        text = font.render("HighScore: " + str(dc), 1, white)
        gameDisplay.blit(text, (display_width - 300, 0))
    if dc < score[0]:
        font = pygame.font.SysFont(None, 25)
        text = font.render("HighScore: " + val, 1, white)
        gameDisplay.blit(text, (display_width - 300, 0))


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def displaylevel(level):
    font = pygame.font.Font(None, 25)
    text = font.render('LEVEL %s' % level, 1, white)
    gameDisplay.blit(text, (display_width / 2-150, 0))

def levelup(level,dc,speed):
    if level == 1:
        speed+=1
        return [level,speed]
    elif level == 2:
        if dc % 5 == 0:
            speed += 2
            return [level, speed]
    elif level == 3:
        if dc % 5 == 0:
            speed  += 5
            return [level, speed]
    return [level, speed]


def life(num):
    heart = pygame.image.load("heart.png")
    gameDisplay.blit(heart, (display_width-50, 0))
    font = pygame.font.Font(None, 25)
    text = font.render('%s' % num, 1, white)
    gameDisplay.blit(text, (display_width -15, 10))

# def shoot(health,x,height,y):
#     bullet = pygame.image.load("missile1.png")
#     for i in range(height,ynew):
#         if x == bullet.x:
#             if bullet.y > y+height:
#                 health -= 5
#                 ynew =
#         if health==0:
#             thing_explode()

def game_loop(doge_count,level,life_num):
    pygame.mixer.music.play(-1)
    x = display_width * 0.4
    y = display_height * 0.8
    x_change = 0
    thing_startx = random.randrange(0, display_width - 100)
    heart_startx = random.randrange(0, display_width - 100)
    thing_starty = 30
    thing_speed = 12
    thing_width = 50
    thing_height = 50
    thing_health=10
    thing_count=1
    i=0
    j=0
    gameExit = False
    while not gameExit:
        thing_yPos = thing_starty+ thing_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
#Uncomment the section and indent it under for loop for controlling the game over keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -20
                if event.key == pygame.K_RIGHT:
                    x_change = 20
                if event.key == pygame.K_SPACE:
                    print(thing_yPos)
                    print(thing_startx)
                    pygame.mixer.Sound.play(fire)
                    #shoot(thing_health,thing_startx,thing_yPos)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0

        x += x_change
        gameDisplay.fill(colors[level])
        gameDisplay.fill(black,(0,0,display_width,30))
        rocket(x, y)
        things_doged(doge_count)
        life(life_num)
        things(thing_startx, thing_starty, thing_width, thing_height, black)
        thing_starty += thing_speed
        displaylevel(level)
        if thing_starty > display_height:
            thing_starty = 0 - thing_height
            thing_startx = random.randrange(0, display_width - 100)
            doge_count += 1
            if doge_count>5:
                li = levelup(1,doge_count,thing_speed)
                if doge_count > 15:
                    li = levelup(2,doge_count,thing_speed)
                    if doge_count > 30:
                        li = levelup(3,doge_count,thing_speed)
                level = li[0]
                thing_speed = li[1]

        if level==2:
            pygame.draw.rect(gameDisplay, black, (20+i , 30, display_width - 40 - 2*i, display_height - 60), 5)
            i += 2
            j+=2
            if i>=50:
                i-=2
                j-=2
        if thing_starty + thing_height > display_height-80:
            if x > thing_startx and x < thing_startx + thing_width or x + rocket_width -10> thing_startx and x + rocket_width -10< thing_startx + thing_width:
                life_num -= 1
                if life_num == 0:
                    crash(doge_count, level)
        if x> display_width-rocket_width or x<0:
            x-=x_change
        highscore(doge_count)
        # Uncomment the section below for controlling the game over Accelerometer console
        """
                list = getInput()
                pitch = list[0]
                roll = list[1]
                if (pitch < 0):
                    x_left = translate(pitch, -40, -1.2, 0, display_width * 0.4)
                    x = x_left
                elif (pitch >= 0):
                    x_right = translate(pitch, -1.2, 50, display_width * 0.4, display_width)
                    x = x_right      
        """
        pygame.display.update()
        clock.tick(30)


def quit():
    pygame.quit()
    sys.exit()


game_intro()
pygame.quit()
sys.exit()
