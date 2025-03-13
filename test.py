import sys

if len(sys.argv) != 2:
    print("Usage: python main.py <value>")
    sys.exit(1)
print('hehe')
value = int(sys.argv[1])

print(value)
