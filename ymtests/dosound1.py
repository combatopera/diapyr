mixer.put() # All off.
A_level.put(0x00)
B_level.put(0x00)
C_level.put(0x00)
sleep(2)
A_level.put(0x0d)
sleep(2)
A_level.put(0x00)
A_level.put(0x0f)
A_level.put(0x00)
sleep(3)
A_level.put(0x0d)
sleep(3)
setprev(0x10)
A_level.anim(-1, 0x0d)
setprev(0x10)
A_level.anim(-2, 0x0d)