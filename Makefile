run:
	@clear; python3 src/pyssembly

runfile:
	@clear; python3 src/pyssembly -f $(file)

runfile-debug:
	@clear; python3 src/pyssembly -f $(file) -d

opdict:
	@clear; python3 src/chunk.py
