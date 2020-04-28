all: buff

buff:
	gcc -g -O0 -fno-stack-protector -fsanitize=address -fsanitize=leak -fsanitize=undefined -fno-omit-frame-pointer -ftest-coverage -fprofile-arcs buff.c -o buff

clean:
	rm buff
