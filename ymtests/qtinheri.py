mixer.put(A_tone)
A_level.put(0x0f)
B_level.put(0x00)
def spike(): # Doesn't work, never mind.
  B_level.put(0x0d)
  B_level.put(0x00)
A_fine.put(0x00)
for i in xrange(20):
  spike()
  A_rough.put(0x0e)
  sleep(2 + i)
  spike()
  A_rough.put(0x02)
  sleep(2 + i)
A_level.put(0x00)
B_level.put(0x00)