# Parser for memory in ESP8266 map
import struct
import sys
import argparse
import itertools


class Parser:

    # States of automata (functions)
    state = ""
    # Header type: 0xe9 basic, 0xea extended
    type_header = None
    # Number of segments in the header
    n_segments = 0
    # Definition of SPI FLASH interface
    spi_flash_interface = 0
    # Mem size
    mem = 0
    # Mem clk
    clk = 0
    # Entry point for block
    entry_point = 0
    # Not used
    c_segment = 0
    # Offset for block
    offset = 0
    # Size of block
    size = 0
    # Calculated address
    address = 0
    # First block expected
    first = True

    def __init__(self, file):
        self.file = file
        self.it = self.bytes_from_file(self.file)

    def read_uint32(self):
        b = bytearray(itertools.islice(self.it,4))
        n = struct.unpack('<L', b)[0]
        return n

    # Read byte in chunks
    def bytes_from_file(self, filename, chunksize=8192):
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(chunksize)
                if chunk:
                    for b in chunk:
                        self.address += 1
                        yield b
                else:
                    break

    # Find header state, look for header bytes
    def find_header(self):
        try:
            self.type_header = next(self.it)
        except:
            self.type_header = None
        if self.type_header is None:
            return None
        # Basic header
        elif self.type_header == 0xe9 and self.first:
            # Read header and jump to first segment
            self.n_segments = next(self.it)
            self.c_segment = 0
            self.spi_flash_interface = next(self.it)
            n = next(self.it)
            self.mem = (n & 0xf0) >> 4
            self.clk = n & 0x0f
            self.entry_point = self.read_uint32()
            print()
            print (f"Header tipo {self.type_header:X}   [{self.address-0x08:08X}]: {self.n_segments} segmentos ------ "
                   f"Entry point: {self.entry_point:X}")
            print ("------------------------------------------------------------------------------------")
            self.first = False
            return self.segment
        # Extended header
        elif self.type_header == 0xea:
            # Read header and jump to first segment
            self.n_segments = next(self.it)
            self.c_segment = 0
            self.spi_flash_interface = next(self.it)
            n = next(self.it)
            self.mem = (n & 0xf0) >> 4
            self.clk = n & 0x0f
            self.entry_point = self.read_uint32()
            print()
            print(
                f"Header tipo {self.type_header:X}   [{self.address-0x08:08X}]: {self.n_segments} segmentos ------ "
                f"Entry point: {self.entry_point:X}")
            print("------------------------------------------------------------------------------------")

            # Reject false headers
            if self.n_segments > 4:
                print("SKIP!!!")
                return self.find_header
            else:
                return self.segment
        else:
            return self.find_header

    # Look for segments state
    def segment(self):
        # Read header and jump to first segment
        self.offset = self.read_uint32()
        self.size = self.read_uint32()
        if self.offset != 0:
            print(f"Segmento #{self.c_segment} de {self.n_segments} [{self.address:08X}] ------ Offset: "
                  f"{self.offset:08X} Size: {self.size:08X} ")
        else:
            # ESP8266ROM.IROM_MAP_START + flashing_addr + 8
            print(f"Segmento #{self.c_segment} de {self.n_segments} [{self.address:08X}] ------ Calc:   "
                  f"{0x40200000:08X} Size: {self.size:08X} ")

        b = bytearray(itertools.islice(self.it, self.size))
        self.c_segment += 1
        if self.type_header == 0xea and self.c_segment == 1:
            b = bytearray(itertools.islice(self.it, 8))
        if self.c_segment < self.n_segments:
            return self.segment
        else:
            return self.find_header

    # Execute states until end
    def run(self):
        if self.state is None:
            return False
        elif type(self.state) == str:
            self.state = self.find_header
            return True
        else:
            self.state = self.state()
            return True


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="image file to parse",
                        action="store", type=str, default=[0])
    args = parser.parse_args()

    p = Parser(args.file)

    while p.run():
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
