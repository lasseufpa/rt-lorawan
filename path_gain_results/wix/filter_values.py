for i in range(100):
    input_file = f"{i}.csv"
    output_file = f"{i}.csv"
    with open(input_file, "r") as fin, open(output_file, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            
            cols = line.split(",")
            last_value = float(cols[-1])

            if last_value >= -200:
                fout.write(line + "\n")