path = r"d:\Backup-STUDY-7-22-2018\AI_Swimming_Data_Bank\data\raw\2023_2024\2023A_Lba_Imx_Distance_Challenge\Meet Results-2023A LBA IMX Distance Challenge-29Dec2023-001.cl2"
with open(path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

for line in lines[:10]:
    print(f"Record: {line[:2]}")
    # Print the line itself
    print(line.rstrip())
    # Print ruler
    ruler = "".join([str(i % 10) for i in range(len(line))])
    print(ruler)
    print()
