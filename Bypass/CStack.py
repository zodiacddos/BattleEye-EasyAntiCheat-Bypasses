import struct

class CStack():
    def __init__(self, data, start_index, size):
        self._data = data
        self._stack_ptr = start_index
        self._size = size
        self._start_address = start_index
    
    def populate_stack(self, data, start_index, insert_data):
        data_packed = ""
        self._data = data
        for d in insert_data:
            packed = struct.pack("<I",d)
            data_packed += packed
        self._data[start_index: start_index + len(data_packed)] = list(data_packed)
        self._stack_ptr = start_index
        self._start_address = start_index
        self._size = len(data_packed)

    def push_word(self, value):
        self._stack_ptr -= 2
        packed_word = struct.pack("<H", value)
        self._data[self._stack_ptr: self._stack_ptr + 2] = list(packed_word)

    def push_dword(self, value):
        self._stack_ptr -= 4
        packed_word = struct.pack("<I", value)
        self._data[self._stack_ptr: self._stack_ptr + 4] = list(packed_word)
        
    def pop_word(self):
        unpacked_word = struct.unpack("<H", "".join(self._data[self._stack_ptr: self._stack_ptr + 2]))[0]
        self._stack_ptr += 2
        return unpacked_word

    def pop_dword(self):    
        unpacked_word = struct.unpack("<I", "".join(self._data[self._stack_ptr: self._stack_ptr + 4]))[0]
        self._stack_ptr += 4
        return unpacked_word

    def pop_dword_but_inc_word(self):
        unpacked_word = struct.unpack("<I", "".join(self._data[self._stack_ptr: self._stack_ptr + 4]))[0]
        self._stack_ptr += 2
        return unpacked_word

    def peek_stack_byte(self, index):
        unpacked_word = struct.unpack("<B", "".join(self._data[index: index + 1]))[0]
        return unpacked_word

    def peek_stack_word(self, index):
        unpacked_word = struct.unpack("<H", "".join(self._data[index: index + 2]))[0]
        return unpacked_word

    def peek_stack_dword(self, index):
        unpacked_word = struct.unpack("<I", "".join(self._data[index: index + 4]))[0]
        return unpacked_word
        
    def pook_stack_byte(self, index, value):
       packed_value = struct.pack("<B", value)
       self._data[index: index + 1] = list(packed_value)

    def pook_stack_word(self, index, value):
       packed_value = struct.pack("<H", value)
       self._data[index: index + 2] = list(packed_value)

    def pook_stack_dword(self, index, value):
        packed_value = struct.pack("<I", value)
        self._data[index: index + 4] = list(packed_value)

    def get_stack_ptr(self):
        return self._stack_ptr
    
    def set_stack_ptr(self, value):
        self._stack_ptr = value
    
    def get_data(self):
        return self._data
    
    def print_stack(self):
        print "~Stack~"
        dst = "[*] Current stack ptr: {0}\n".format(hex(self._stack_ptr))
        if self._stack_ptr > self._start_address:
            for i in range(self._stack_ptr + 16, self._start_address, -4):
                dst += "{}: ".format(hex(i - 4))
                dst += hex(struct.unpack("<I", "".join(self._data[i - 4:i]))[0])
                if i - 4 <= self._stack_ptr < i:
                    dst += '\t <---'
                dst += '\n'
        for i in range(0, self._size, 4):
            dst += "{}: ".format(hex(self._start_address - i))
            dst += hex(struct.unpack("<I", "".join(self._data[self._start_address -  (i+4):self._start_address -i]))[0])
            if self._start_address - (i + 4) <= self._stack_ptr < self._start_address - i:
                dst += '\t <---'
            dst += '\n'
        
        print dst

    def get_size(self):
        return len(self._data)