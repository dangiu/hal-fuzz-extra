UNICORN_QEMU_FLAGS="--python=/usr/bin/python3" make
cd ./unicorn_mode
sudo ./build_unicorn_support.sh
cd ..
cd hal_fuzz
sudo pip3 install -e .
cd hal_fuzz/native
make
cd ../../../
