import json, sys, pathlib, traceback

p = pathlib.Path(r"C:\Users\danys\Desktop\Lavoro\NTT Data\16-10\app\state.json")
try:
    with p.open('r', encoding='utf-8') as f:
        data = json.load(f)
    print('VALID')
    print('Top keys:', ','.join(list(data.keys())))
    print('cookies count:', len(data.get('cookies', [])))
    print('origins count:', len(data.get('origins', [])))
except Exception as e:
    print('INVALID')
    traceback.print_exc()
    sys.exit(1)
