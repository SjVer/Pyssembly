.PHONY: test
test: prepare
	@#spython3 src/pyssembly -c $(file) -o ./bin
	@python3 src/pyssembly -r ./bin #$(notdir $(basename $(file)))

.PHONY: test-debug
test-debug: prepare
	@#python3 src/pyssembly -c $(file) -o ./bin -d
	@python3 src/pyssembly -r ./bin -d -s #$(notdir $(basename $(file))) -d -s

clean:
	@rm -r ./bin #$(notdir $(basename $(file)))

.PHONY: profile
profile:
	@#python3 src/pyssembly -c $(file) -o ./bin
	@kernprof -l src/pyssembly -c $(file) -o ./bin
	@kernprof -l src/pyssembly -r ./bin #$(notdir $(basename $(file)))
	@python3 -m line_profiler pyssembly.lprof
	@rm pyssembly.lprof

.PHONY: profile-vm
profile-vm:
	@kernprof -l src/vm.py
	@python3 -m line_profiler vm.py.lprof
	@rm vm.py.lprof

.PHONY: prepare
prepare:
	@python3 src/pyssembly -c $(file) -o ./bin
	@cp -r include/* bin/