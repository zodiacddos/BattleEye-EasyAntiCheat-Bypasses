# This script if to open the Main.exe, not the dll or the service, but the exe itself.
import ctypes
import struct
from CStack import CStack
from ASMFlags import ASMFlags
rol = lambda val, r_bits, max_bits: \
    (val << r_bits%max_bits) & (2**max_bits-1) | \
    ((val & (2**max_bits-1)) >> (max_bits-(r_bits%max_bits)))
 
# Rotate right: 0b1001 --> 0b1100
ror = lambda val, r_bits, max_bits: \
    ((val & (2**max_bits-1)) >> r_bits%max_bits) | \
    (val << (max_bits-(r_bits%max_bits)) & (2**max_bits-1))

def shrd_with_flags(dest, src, cl, size):
    cl = cl % 32
    dest >>= cl
    src = (src << (size - cl)) & ((2 ** size) - 1)
    dest = src | dest
    flags = ASMFlags()
    last_pushed = dest & (cl ** 2)
    if last_pushed != 0:
        flags.set_carry()
    if 2 ** size & dest == 1:
        flags.set_sign()
    if dest == 0:
        flags.set_zero()
    if count_bits(dest) % 2 == 0:
        flags.set_parity()
    return flags, dest

def shld_with_flags(dest, src, cl, size):
    cl = cl % 32
    dest = (dest << cl) & ((2 ** size) - 1)
    src = src >> (size - cl)
    dest = src | dest
    flags = ASMFlags()
    last_pushed = dest & (cl ** 2)
    if last_pushed != 0:
        flags.set_carry()
    if 2 ** size & dest == 1:
        flags.set_sign()
    if dest == 0:
        flags.set_zero()
    if count_bits(dest) % 2 == 0:
        flags.set_parity()
    return flags, dest


def count_bits(value):
    bits_sum = 0
    value = ctypes.c_uint(value).value
    while value:
        if value & 1:
            bits_sum += 1
        value >>= 1
    return bits_sum

def pop_from_stack_to_variable(unpacker):
    pop_place = struct.unpack("<B",read_data(unpacker.get_ip_opcode()))[0]
    pop_place = ctypes.c_uint8(pop_place ^ (unpacker.get_xor_key() & 0xff)).value
    pop_place = ctypes.c_uint8(pop_place ^ 0x7C).value
    pop_place = ctypes.c_uint8(~pop_place).value 
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    unpacker.set_xor_key(((unpacker.get_xor_key() & 0xff) ^ pop_place) + (unpacker.get_xor_key() & 0xffffff00))
    pop_place /= 4 # we need to align the pop place to 4 bytes for each reg, like the stack align.
    stack_value = unpacker.pop_dword_from_stack()
    unpacker.set_reg_value(pop_place, stack_value)
    print "[+] Pop from stack to reg r{0} the value of {1}".format(pop_place, hex(stack_value))

def push_dword_from_optable(unpacker):
    enc_key = get_dword_from_address(unpacker.get_ip_opcode())
    enc_key = ctypes.c_uint32(enc_key + unpacker.get_xor_key()).value
    enc_key = ror(enc_key, 6, 32)
    enc_key =  ctypes.c_uint32(enc_key ^ 0x0A37E6943).value
    enc_key -= 1
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 4)
    unpacker.set_xor_key(ctypes.c_uint32(unpacker.get_xor_key() + enc_key).value)
    unpacker.push_dword(enc_key)
    print "[+] Push dword into stack from iptable {0}".format(hex(enc_key))

def do_dword_addition_on_stack_push_flags(unpacker):
    top_of_stack = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    value_2 = ctypes.c_uint32(unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 4)).value
    new_val = ctypes.c_uint32(value_2 + top_of_stack).value
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 4, new_val)

    flags = ASMFlags()
    if new_val == 0: # set the zero flags
        flags.set_zero()
    if count_bits(new_val) % 2 == 0:# number of bits even
        flags.set_parity()
    if new_val & 0x80000000:# the msb is 1
        flags.set_sign()
    if top_of_stack + value_2 > 0xffffffff:
        flags.set_carry()
    if (value_2 & 0x7f000000 and (top_of_stack + value_2) & 0x80000000) or (value_2 & 0x80000000 and (top_of_stack + value_2) & 0x7f000000): # Set overflow
        flags.set_overflow()
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Dword addition - add 2 dwords from the stack, value {0} and flags {1}".format(hex(new_val), hex(flags.get_binary()))

def push_reg_value_into_stack(unpacker):
    reg_index = struct.unpack("<B",read_data(unpacker.get_ip_opcode()))[0]
    reg_index ^= unpacker.get_xor_key() & 0xff
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    reg_index ^= 0x7C
    reg_index = ctypes.c_uint8(~reg_index).value
    unpacker.set_xor_key(((unpacker.get_xor_key() & 0xff) ^ reg_index) + (unpacker.get_xor_key() & 0xffffff00))
    unpacker.push_dword(unpacker.get_reg_value(reg_index / 4))
    print "[+] Reg dword push - Push reg to stack, reg index: {0}, reg value: {1}".format(hex(reg_index / 4), hex(unpacker.get_reg_value(reg_index / 4)))
    
def push_stack_ptr(unpacker):
    stack_index = unpacker.get_stack_ptr()
    unpacker.push_dword(stack_index) 
    print "[+] Pushed the last stack addr: {0}".format(hex(stack_index))


def push_word_into_stack(unpacker):
    value = struct.unpack("<B",read_data(unpacker.get_ip_opcode()))[0]
    value = ctypes.c_uint8(value + (unpacker.get_xor_key() & 0xff)).value
    value = ror(value, 7, 8)
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    value = ctypes.c_uint8(value + 1).value
    value = rol(value, 4, 8)
    unpacker.push_word(value)
    unpacker.set_xor_key((ctypes.c_uint8((unpacker.get_xor_key() & 0xff) + value)).value + (unpacker.get_xor_key() & 0xffffff00)) 
    print "[+] Pushed word value: {0} into stack".format(value)
    
def read_from_data_push_word(unpacker):
    value = unpacker.pop_dword_but_inc_word()
    if value < IMAGE_BASE:
        data = get_byte_from_process_data(value)
    else:
        data = struct.unpack("<B",read_data(value))[0]
    unpacker.pook_stack_word(unpacker.get_stack_ptr(), data)
    print "[*] Byte read - Read value {0} at address {1}".format(hex(data), hex(value))

def get_stack_value_at_offset(unpacker):
    offset = unpacker.pop_dword_but_inc_word()
    byte_value = unpacker.peek_stack_byte(offset)
    unpacker.pook_stack_word(unpacker.get_stack_ptr(), byte_value)
    print "[+] Read byte from stack write to offset - Read value from stack: {0} write it to: {1}".format(byte_value, hex(offset))

def store_and_result_and_flags(unpacker):
    value_1 = unpacker.peek_stack_word(unpacker.get_stack_ptr())
    value_2 = unpacker.peek_stack_word(unpacker.get_stack_ptr() + 2)
    value_1 = (value_1 & 0xff00) + ctypes.c_uint8(~(value_1 & 0xff)).value
    value_2 = (value_2 & 0xff00) + ctypes.c_uint8(~(value_2 & 0xff)).value
    value_1 = (value_1 & 0xff00) + ((value_1&0xff) & (value_2 &0xff))
    value_lower = ((value_1&0xff) & (value_2 &0xff))
    flags = ASMFlags() # get flags to push
    if value_lower == 0: # set the zero flags
        flags.set_zero()
    if count_bits(value_lower) % 2 == 0:# number of bits even
        flags.set_parity()
    if value_lower & 0x80:# the msb is 1
        flags.set_sign()

    unpacker.set_stack_ptr(unpacker.get_stack_ptr() - 2)
    unpacker.pook_stack_word(unpacker.get_stack_ptr() + 4, value_1)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] And operation(byte) - Set value {0} at stack pushed flags to stack {1}".format(hex(value_1), hex(flags.get_binary()))

def add_byte_to_stack_store_flags(unpacker):
    value_1 = unpacker.peek_stack_byte(unpacker.get_stack_ptr())
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() - 2)    
    value_2 = unpacker.peek_stack_byte(unpacker.get_stack_ptr() + 4)
    value_1 = ctypes.c_uint8(value_1 + value_2).value

    flags = ASMFlags() # get flags to push
    if value_1 == 0: # set the zero flags
        flags.set_zero()
    if count_bits(value_1) % 2 == 0:# number of bits even
        flags.set_parity()
    if value_1 & 0x80:# the msb is 1
        flags.set_sign()
    if value_1 + value_2 > 0xff:
        flags.set_carry()
    if (value_2 & 0x7f and (value_1 + value_2) & 0x80) or (value_2 & 0x80 and (value_1 + value_2) & 0x7f): # Set overflow
        flags.set_overflow()

    unpacker.pook_stack_byte(unpacker.get_stack_ptr() + 4, value_1)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Addition (byte) - Pushed value: {0} to stack with flags {1}".format(value_1, hex(flags.get_binary()))

def pop_byte_to_reg(unpacker):
    value = struct.unpack("<B",read_data(unpacker.get_ip_opcode()))[0]
    value = ctypes.c_uint8(value + (unpacker.get_xor_key() & 0xff)).value
    value = rol(value, 3, 8)
    value = ctypes.c_uint8(value + 1).value
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    value = rol(value, 4, 8)
    unpacker.set_xor_key((ctypes.c_uint8((unpacker.get_xor_key() & 0xff) + value)).value + (unpacker.get_xor_key() & 0xffffff00)) 
    stack_val = unpacker.pop_word_from_stack()

    reg_value = unpacker.get_reg_value(value / 4)
    reg_reminder = value % 4 # this is the index of the semi-reg inside the big reg, we need this for the mast
    mask = 0
    shifting = 0
    if reg_reminder == 0:
        mask = 0x000000ff
        shifting = 0
    elif reg_reminder == 1:
        mask = 0x0000ff00
        shifting = 8
    elif reg_reminder == 2:
        mask = 0x00ff0000
        shifting = 16
    else:
        mask = 0xff000000
        shifting = 24

    reg_value = ctypes.c_uint32((reg_value & (ctypes.c_uint32(~mask).value)) + ((stack_val << shifting) & mask)).value
    unpacker.set_reg_value(value / 4, reg_value)
    print "[+] Pop stack byte write to reg - Set reg {0} new value: {1}".format(hex(value), hex(reg_value))

def get_pointer_value(unpacker):
    stack_offset = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    value_at_offset = unpacker.peek_stack_dword(stack_offset)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), value_at_offset)
    print "[+] Set value {0} at offset {1}".format(hex(value_at_offset), hex(stack_offset))

def store_and_dword_result_and_flag(unpacker):
    value_1 = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    value_2 = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 4)
    value_1 = ctypes.c_uint32(~value_1).value
    value_2 = ctypes.c_uint32(~value_2).value
    value_1 = value_1 & value_2
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 4, value_1)

    flags = ASMFlags() # get flags to push
    if value_1 == 0: # set the zero flags
        flags.set_zero()
    if count_bits(value_1) % 2 == 0:# number of bits even
        flags.set_parity()
    if value_1 & 0x80000000:# the msb is 1
        flags.set_sign()

    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] And operation (dword) - Put value: {0} on the stack with flags: {1}".format(hex(value_1), hex(flags.get_binary()))

def set_dword_value_at_stack(unpacker):
    value = get_word_from_address(unpacker.get_ip_opcode())
    value = ctypes.c_uint16(value - (unpacker.get_xor_key() & 0xffff)).value
    value ^= 0x1476
    value += 0x1ba4
    value = ror(value, 10, 16)
    if ctypes.c_int16(value).value < 0:
        value += 0xffff0000
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 2)
    unpacker.set_xor_key((unpacker.get_xor_key() & 0xffff0000) + ctypes.c_uint16(((unpacker.get_xor_key() & 0xffff) - value)).value)
    unpacker.push_dword(value)
    print "[+] push dword from optable - Pushed value {0} to the stack".format(hex(value))

def push_dword_to_stack(unpacker):
    value = struct.unpack("<B",read_data(unpacker.get_ip_opcode()))[0]
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    value = ctypes.c_uint8(value + unpacker.get_xor_key() & 0xff).value
    value = ror(value, 7, 8)
    value = ctypes.c_uint8(value + 1).value
    value = rol(value, 4, 8)
    unpacker.set_xor_key((ctypes.c_uint8((unpacker.get_xor_key() & 0xff) + value)).value + (unpacker.get_xor_key() & 0xffffff00)) 
    if ctypes.c_int8(value).value < 0:
        value += 0xffffff00
    unpacker.push_dword(value)
    print "[+] push dword from optable - Pushed dword to stack {0}".format(hex(value))

def shift_right(unpacker):
    value = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    tmp_value = value
    value_shift = unpacker.peek_stack_byte(unpacker.get_stack_ptr() + 4)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() - 2)
    value >>= value_shift
    value = ctypes.c_uint(value).value

    #Set flags
    flags = ASMFlags()
    if value == 0: # set the zero flags
        flags.set_zero()
    if count_bits(value) % 2 == 0:# number of bits even
        flags.set_parity()
    if value & 0x80000000:# the msb is 1
        flags.set_sign()
    if (tmp_value >> value_shift - 1) & 0x1:
        flags.set_carry()

    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 4, value)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+]Shift right (Dword) - Pushed value: {0} with flags: {1}".format(hex(value), hex(flags.get_binary()))
    

def pop_optable_pointer(unpacker):
    ipcode = unpacker.pop_dword_from_stack()
    unpacker.set_xor_key(ctypes.c_uint32(ipcode).value)
    mask = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    unpacker.set_ip_opcode(ctypes.c_uint32(mask + ipcode).value)
    print "[*] Set the ipcode ptr to {0}".format(hex(unpacker.get_ip_opcode()))

def stack_pivot(unpacker):
    stack_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    stack = CStack(PROGRAM_DATA, stack_value, 96)
    unpacker.set_stack(stack)
    unpacker.add_stack(stack_value, stack)
    print "[+] Set new stack at value {0}".format(hex(stack_value))

def pop_flags(unpacker):
    flags = unpacker.pop_dword_from_stack()
    print "[+] Popped flags {0}".format(flags)

def write_value_to_address_from_stack(unpacker):
    address = unpacker.pop_dword_from_stack()
    value = unpacker.pop_dword_from_stack()
    if address < IMAGE_BASE: # the address is prob on the stack or something.
        set_dword_at_process_data(address, value)
    else:
        set_dword_to_address(address, struct.pack("<I", value))
    print "[*] Write dword value to address - write From stack address {0} the value of {1}".format(hex(address), hex(value))
    #raw_input()

def call_function_store_result(unpacker):
    opcode = struct.unpack("<B", read_data(unpacker.get_ip_opcode()))[0]
    opcode = ctypes.c_uint8(opcode + (unpacker.get_xor_key() & 0xff)).value
    opcode = ror(opcode, 7, 8)
    opcode = ctypes.c_uint8(opcode + 1).value
    opcode = rol(opcode,4,8)
    unpacker.set_xor_key((ctypes.c_uint8((unpacker.get_xor_key() & 0xff) + opcode)).value + (unpacker.get_xor_key() & 0xffffff00)) 
    address_end_data = unpacker.get_stack_ptr() + opcode* 4
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() - 4, address_end_data)
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    arguments = []
    for i in range(opcode, 0, -1):
        value_at_stack = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + i * 4)
        unpacker.pook_stack_dword(unpacker.get_stack_ptr() + i *4 ,0)
        arguments.append(value_at_stack)
    function_address = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), 0)
    print "[*] Call function at address: {0} with params: {1}".format(hex(function_address), " ".join(hex(i) for i in arguments))
    result = API_CALL_TABLE[function_address](unpacker, *arguments)
    stack_val = unpacker.peek_stack_dword(unpacker.get_stack_ptr() - 4)
    unpacker.set_stack_ptr(stack_val)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), result)
    #raw_input()
    
def load_ptr_to_stack(unpacker):
    read_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    if read_value > IMAGE_BASE:
        if read_value in IMPORT_TABLE:
            value_at_address = IMPORT_TABLE[read_value]
        else:
            value_at_address = get_dword_from_address(read_value)
    else:
        value_at_address = get_dword_from_process_data(read_value)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), value_at_address)
    print "[*] get value from address push to stack - Pushed value {0} to stack from address {1}".format(hex(value_at_address), hex(read_value))

def load_word_reg_into_stack(unpacker):
    value = struct.unpack("<B",read_data(unpacker.get_ip_opcode()))[0]
    value = ctypes.c_uint8(value + (unpacker.get_xor_key() & 0xff)).value
    value = rol(value, 3, 8)
    value = ctypes.c_uint8(value + 1).value
    value = rol(value, 4, 8)
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    unpacker.set_xor_key((ctypes.c_uint8((unpacker.get_xor_key() & 0xff) + value)).value + (unpacker.get_xor_key() & 0xffffff00)) 
    reg_index = value / 4
    reg_reminder = value % 4
    reg_value = unpacker.get_reg_value(reg_index)
    dst_value = 0
    if reg_reminder == 0:
        dst_value = 0xff & reg_value
    elif reg_reminder == 1:
        dst_value = (0x0000ff00 & reg_value) >> 8
    elif reg_reminder == 2:
        dst_value = (0x00ff0000 & reg_value) >> 16
    else:
        dst_value = (0xff000000 & reg_value) >> 24
    
    unpacker.push_word(dst_value)
    print "[+] Push word from reg - Pushed reg word into the stack with value {0}".format(dst_value)

def write_value_to_address(unpacker):
    address = unpacker.pop_dword_from_stack()
    value = unpacker.pop_dword_from_stack()
    if address < IMAGE_BASE:
        set_dword_at_process_data(address, value)
    else:
        set_dword_to_address(address, struct.pack("<I",value))
    print "[*] Write dword - Put From stack value: {0} at address {1}".format(hex(value), hex(address))
    #raw_input()

def run_cpuid(unpacker):
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() - 0xc)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 0xc, CPUID_EAX_VALUE)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 0x8,CPUID_EBX_VALUE)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 0x4,CPUID_ECX_VALUE)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(),CPUID_EDX_VALUE)
    print "[+] Pushed cpuid"

def shld_from_stack(unpacker):
    dst = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    src = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 4)
    cl = unpacker.peek_stack_byte(unpacker.get_stack_ptr() + 8)
    flags, dst = shld_with_flags(dst, src, cl, 32)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() + 2)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 4, dst)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Shlead the value of {0} with flags: {1}".format(hex(dst), hex(flags.get_binary()))

def shrd_from_stack(unpacker):
    dst = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    src = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 4)
    cl = unpacker.peek_stack_byte(unpacker.get_stack_ptr() + 8)
    flags, dst = shrd_with_flags(dst, src, cl, 32)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() + 2)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 4, dst)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Shread the value of {0} with flags: {1}".format(hex(dst), hex(flags.get_binary()))

def write_word_from_stack_to_reg(unpacker):
    value = struct.unpack("<B",read_data(unpacker.get_ip_opcode()))[0]
    value = ctypes.c_uint8(value - (unpacker.get_xor_key() & 0xff)).value
    value = ctypes.c_uint8(value - 1).value
    value = ctypes.c_uint8(~value).value + 1
    value = ctypes.c_uint8(value - 0x37).value
    unpacker.set_xor_key((ctypes.c_uint8((unpacker.get_xor_key() & 0xff) - value)).value + (unpacker.get_xor_key() & 0xffffff00)) 
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    word_value = unpacker.pop_word_from_stack()

    reg_index = value / 4
    reg_reminder = value % 4
    reg_value = unpacker.get_reg_value(reg_index)
    if reg_reminder == 2: #high
        reg_value = (reg_value & 0xffff) | (word_value << 16)
    else: #low
        reg_value = (reg_value & 0xffff0000) | (word_value)
    unpacker.set_reg_value(reg_index, reg_value)
    print "[+] Get word from stack and push to reg - Put reg r{0} to value {1}".format(reg_index,hex(reg_value))

def get_word_ptr_value_from_stack(unpacker):
    address = unpacker.pop_dword_but_inc_word()
    if address < IMAGE_BASE:
        value = get_word_from_process_data(address)
    else:
        value = get_word_from_address(address)
    unpacker.pook_stack_word(unpacker.get_stack_ptr(), value)
    print "[+] Read word from address - Pushed value {0} to the stack from address {1}".format(hex(value), hex(address))

def shift_left_word_from_stack(unpacker):
    value = unpacker.peek_stack_word(unpacker.get_stack_ptr())
    shift_size = unpacker.peek_stack_byte(unpacker.get_stack_ptr() +  2)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() -  2)
    shift_value = (value << shift_size) & (2**16 - 1)
    flags = ASMFlags()
    if shift_value == 0: # set the zero flags
        flags.set_zero()
    if count_bits(shift_value) % 2 == 0:# number of bits even
        flags.set_parity()
    if shift_value & 0x8000:# the msb is 1
        flags.set_sign()
    if ((value <<(shift_size - 1))  & (2**16 - 1)) & 0x8000:
        flags.set_carry()
    
    unpacker.pook_stack_word(unpacker.get_stack_ptr() + 4, shift_value)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Shift left word -  Shift left value and pushed {0} value with flags {1}".format(hex(shift_value), hex(flags.get_binary()))

def shift_left_dword_from_stack(unpacker):
    value = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    shift_size = unpacker.peek_stack_byte(unpacker.get_stack_ptr() +  4)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() -  2)

    shift_value = (value << shift_size) & (2**32 - 1)
    flags = ASMFlags()
    if shift_value == 0: # set the zero flags
        flags.set_zero()
    if count_bits(shift_value) % 2 == 0: # number of bits even
        flags.set_parity()
    if shift_value & 0x80000000:# the msb is 1
        flags.set_sign()
    if ((value <<(shift_size - 1))  & (2**32 - 1)) & 0x80000000:
        flags.set_carry()
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 4, shift_value)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Shift left dword - Shift left value and pushed {0} value with flags {1}".format(hex(shift_value), hex(flags.get_binary()))
    
def load_word_from_reg_to_stack(unpacker):
    reg_value = struct.unpack("<B", read_data(unpacker.get_ip_opcode()))[0]
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 1)
    reg_value = ctypes.c_uint8(reg_value - (unpacker.get_xor_key() & 0xff)).value   
    reg_value = ctypes.c_uint8(reg_value - 1).value
    reg_value = ctypes.c_uint8(ctypes.c_uint8(~reg_value).value + 1).value
    reg_value = ctypes.c_uint8(reg_value - 0x37).value
    unpacker.set_xor_key((ctypes.c_uint8((unpacker.get_xor_key() & 0xff) - reg_value)).value + (unpacker.get_xor_key() & 0xffffff00)) 
    reg_index = reg_value / 4
    reg_offset = reg_value % 4
    value = unpacker.get_reg_value(reg_index)
    if reg_offset == 0: #high
        value = (value & 0xffff)
    else: #low
        value = ((value & 0xffff0000) >> 16)
    unpacker.push_word(value)
    print "[+] Pushed word reg value into the stack {0}, reg index: r{1}".format(hex(value), reg_index / 4) 

def write_byte_to_address(unpacker):
    address = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    value = unpacker.peek_stack_byte(unpacker.get_stack_ptr() + 4)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() + 6)
    if address < IMAGE_BASE:
        set_byte_at_process_data(address, value)
    else:
        set_byte_at_address(address, value)
    print "[*] Get address and write byte - Put value {0} at address {1}".format(hex(value),hex(address))

def get_word_address_from_stack_and_push(unpacker):
    address = unpacker.pop_dword_but_inc_word()
    if address < IMAGE_BASE:
        value = get_word_from_process_data(address)
    else:
        value = get_word_from_address(address)
    unpacker.pook_stack_word(unpacker.get_stack_ptr(), value)
    print "[+] Get word from address - Pushed value {0} from {1} to the stack".format(hex(value),hex(address))

def write_word_to_address(unpacker):
    address = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    value = unpacker.peek_stack_word(unpacker.get_stack_ptr() + 4)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() + 6)
    if address < IMAGE_BASE:
        set_word_at_process_data(address, value)
    else:
        set_word_to_address(address, struct.pack("<H",value))
    print "[*] Write word to address - Put value {0} at adddress {1}".format(hex(value), hex(address))

def write_to_address_from_stack_dword(unpacker):
    address = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 4)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() + 8)
    if address < IMAGE_BASE:
        set_dword_at_process_data(address, value)
    else:
        set_dword_to_address(address, struct.pack("<I", value))
    print "[*] Write dword to address - Put Stack address {0} value {1}".format(hex(address), hex(value))
    #raw_input()

def add_word_to_stack_pos(unpacker):
    value = unpacker.peek_stack_word(unpacker.get_stack_ptr())
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() - 2)
    stack_value = unpacker.peek_stack_word(unpacker.get_stack_ptr() + 4)
    value_1 = ctypes.c_uint16(value + stack_value).value

    flags = ASMFlags() # get flags to push
    if value_1 == 0: # set the zero flags
        flags.set_zero()
    if count_bits(value_1) % 2 == 0:# number of bits even
        flags.set_parity()
    if value_1 & 0x8000:# the msb is 1
        flags.set_sign()
    if value + stack_value > 0xffff:
        flags.set_carry()
    if (stack_value & 0x7fff and (value + stack_value) & 0x8000) or (stack_value & 0x8000 and (value + stack_value) & 0x7fff): # Set overflow
        flags.set_overflow()
    unpacker.pook_stack_word(unpacker.get_stack_ptr() + 4, value_1)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Addition (word) Added word to stack sum {0} flags {1}".format(hex(value_1),hex(flags.get_binary()))

def write_word_to_stack_from_optable(unpacker):
    value = get_word_from_address(unpacker.get_ip_opcode())
    value = ctypes.c_uint16(value - (unpacker.get_xor_key() & 0xffff)).value
    value = ctypes.c_uint16(value ^ 0x1476).value
    value = ctypes.c_uint16(value + 0x1ba4).value
    unpacker.set_ip_opcode(unpacker.get_ip_opcode() + 2)
    value = ror(value, 10, 16)
    unpacker.set_xor_key((unpacker.get_xor_key() & 0xffff0000) + ctypes.c_uint16(((unpacker.get_xor_key() & 0xffff) - value)).value)
    unpacker.push_word(value)
    print "[+] Pushed word into stack {0}".format(hex(value))

def shift_left_byte_from_stack(unpacker):
    value = unpacker.peek_stack_byte(unpacker.get_stack_ptr())
    shift_size = unpacker.peek_stack_byte(unpacker.get_stack_ptr() + 2)
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() - 2)
    shifted_value = (value << shift_size) & ((2 ** 8 )- 1)
    flags = ASMFlags()
    if (value << (shift_size - 1)) & (2 ** 8):
        flags.set_carry()
    if shifted_value == 0:
        flags.set_zero()
    if count_bits(shifted_value) % 2 == 0:
        flags.set_parity()
    if shifted_value & 0x80:
        flags.set_sign()
    unpacker.pook_stack_word(unpacker.get_stack_ptr() + 4, shifted_value)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Shifted left byte, value {0} flags {1}".format(hex(shifted_value), hex(flags.get_binary()))

def nand_word_stack(unpacker):
    stack_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    stack_value = ctypes.c_uint32(~stack_value).value
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), stack_value)
    ax_value = stack_value & 0xffff
    unpacker.set_stack_ptr(unpacker.get_stack_ptr() - 2)
    next_stack_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 4)
    next_stack_value = (next_stack_value&0xffff0000) +  (next_stack_value & ax_value)
    flags = ASMFlags() # get flags to push
    if next_stack_value == 0: # set the zero flags
        flags.set_zero()
    if count_bits(next_stack_value) % 2 == 0:# number of bits even
        flags.set_parity()
    if next_stack_value & 0x8000:# the msb is 1
        flags.set_sign()
    unpacker.pook_stack_dword(unpacker.get_stack_ptr() + 4, next_stack_value)
    unpacker.pook_stack_dword(unpacker.get_stack_ptr(), flags.get_binary())
    print "[+] Nand word into the stack, value {0} flags {1}".format(hex(next_stack_value), hex(flags.get_binary()))


def rdtsc(unpacker):
    ebx_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr())
    edx_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 4)
    ebp_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 8)
    eax_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 12)
    esi_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 16)
    edx_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 20)
    ecx_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 24)
    edi_value = unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 28)
    print "[+] Return to {0}".format(hex(unpacker.peek_stack_dword(unpacker.get_stack_ptr() + 44)))
    for i in range(0, 0x68, 4):
        print hex(get_dword_from_process_data(0x3f0e0 +i))

OP_DICT = {
    0x7b: pop_from_stack_to_variable,
    0x98: push_dword_from_optable,
    0x3d: do_dword_addition_on_stack_push_flags,
    0x43: pop_from_stack_to_variable,
    0xae: pop_from_stack_to_variable,
    0x63: pop_from_stack_to_variable,
    0x0e: pop_from_stack_to_variable,
    0x73: push_reg_value_into_stack,
    0x5b: push_dword_from_optable, 
    0xe2: push_stack_ptr,
    0x7e: push_word_into_stack,
    0x44: do_dword_addition_on_stack_push_flags,
    0x2a: read_from_data_push_word,
    0x39: get_stack_value_at_offset,
    0x79: store_and_result_and_flags,
    0x3f: add_byte_to_stack_store_flags,
    0xe7: push_stack_ptr,
    0x5e: get_stack_value_at_offset,
    0x0a: store_and_result_and_flags,
    0xdf: pop_byte_to_reg,
    0x05: get_pointer_value,
    0x06: store_and_dword_result_and_flag,
    0x02: set_dword_value_at_stack,
    0x25: store_and_dword_result_and_flag,
    0x87: push_reg_value_into_stack,
    0x6f: set_dword_value_at_stack,
    0xbe: push_word_into_stack,
    0x3e: get_pointer_value,
    0x76: push_dword_to_stack,
    0x4d: shift_right,
    0xb1: do_dword_addition_on_stack_push_flags,
    0xcc: push_stack_ptr,
    0x66: store_and_dword_result_and_flag,
    0x26: store_and_dword_result_and_flag,
    0xf5: pop_from_stack_to_variable,
    0xb7: push_dword_from_optable, 
    0x35: pop_optable_pointer,
    0xf4: get_pointer_value,
    0xc7: store_and_dword_result_and_flag,
    0x19: push_dword_to_stack,
    0xa4: push_dword_to_stack,
    0x51: stack_pivot,
    0x70: store_and_dword_result_and_flag,
    0x10: set_dword_value_at_stack,
    0xc4: do_dword_addition_on_stack_push_flags,
    0x45: pop_flags,
    0x5c: write_value_to_address_from_stack,
    0xa2: push_dword_from_optable,
    0x90: push_dword_to_stack,
    0xf3: pop_from_stack_to_variable,
    0xd8: pop_from_stack_to_variable,
    0xc9: call_function_store_result,
    0x86: do_dword_addition_on_stack_push_flags,
    0xeb: pop_optable_pointer,
    0x8a: push_word_into_stack,
    0x11: shift_right, 
    0xca: pop_from_stack_to_variable,
    0xa9: load_ptr_to_stack,
    0x30: set_dword_value_at_stack,
    0x29: load_word_reg_into_stack,
    0x03: store_and_result_and_flags,
    0x81: load_word_reg_into_stack,
    0x31: store_and_result_and_flags,   
    0x47: pop_byte_to_reg,
    0x1a: shift_right,
    0xd5: push_dword_to_stack,
    0x91: push_dword_to_stack,
    0x72: pop_optable_pointer,
    0x07: load_ptr_to_stack,
    0x8b: get_pointer_value,
    0xfe: pop_from_stack_to_variable,
    0xee: load_word_reg_into_stack,
    0x9f: load_word_reg_into_stack,
    0x9b: push_word_into_stack,
    0x53: pop_optable_pointer,
    0x37: write_value_to_address,
    0x3a: shift_right,
    0x22: shift_right,
    0xec: run_cpuid,
    0x04: shrd_from_stack,
    0x6a: write_word_from_stack_to_reg,
    0xe4: read_from_data_push_word,
    0x7c: get_word_ptr_value_from_stack,
    0x32: shift_left_dword_from_stack,
    0x7a: load_word_from_reg_to_stack,
    0xe6: load_word_from_reg_to_stack,
    0x0d: shift_left_dword_from_stack,
    0x6d: write_word_from_stack_to_reg,
    0xc0: get_word_ptr_value_from_stack,
    0x2c: shrd_from_stack,
    0x33: load_word_from_reg_to_stack,
    0x68: load_word_from_reg_to_stack,
    0x85: shld_from_stack,
    0x00: shld_from_stack,
    0x24: shift_left_dword_from_stack,
    0x99: shrd_from_stack,
    0x89: get_word_ptr_value_from_stack,
    0xff: set_dword_value_at_stack,
    0xc8: push_dword_to_stack,
    0x75: write_word_from_stack_to_reg,
    0xcd: shld_from_stack,
    0xcf: write_word_from_stack_to_reg,
    0x38: shift_left_dword_from_stack,
    0xd0: load_word_from_reg_to_stack,
    0x5a: shift_left_dword_from_stack,
    0x9d: set_dword_value_at_stack,
    0x97: call_function_store_result,
    0x8f: load_word_reg_into_stack,
    0xad: get_stack_value_at_offset,
    0xb3: store_and_result_and_flags,
    0xe8: add_byte_to_stack_store_flags,
    0xc5: store_and_result_and_flags,
    0x94: pop_byte_to_reg,
    0x1d: write_byte_to_address,
    0x20: stack_pivot,
    0xbf: pop_flags,
    0x4e: run_cpuid,
    0x1e: write_to_address_from_stack_dword,
    0x62: shift_right,
    0x12: write_byte_to_address,
    0x59: write_to_address_from_stack_dword,
    0x96: add_word_to_stack_pos,
    0x7f: write_word_from_stack_to_reg,
    0xdd: shift_left_word_from_stack,
    0x54: write_word_to_stack_from_optable,
    0xda: write_to_address_from_stack_dword,
    0x69: shift_left_dword_from_stack,
    0x49: shift_left_byte_from_stack,
    0x8e: write_word_to_stack_from_optable,
    0xef: write_word_to_address,
    0x6e: nand_word_stack,
    0xf1: write_word_to_stack_from_optable,
    0xe9: pop_flags,
    0x3b: write_byte_to_address,
    0x0f: shift_left_word_from_stack,
    0x2b: rdtsc
}


DATA = ""
OP_TABLE_ADDRESS = 0x8d1a9 + IMAGE_BASE
MASK = 0x640000
ENTRY_POINT_ADDRESS = 0x7e607 + IMAGE_BASE
PEB_DEFAULT_VALUE = 0x00DC0000
EPB_DEFAULT_VALUE = 0x0099F8B8  
PROGRAM_DATA = ['\x00'] * IMAGE_BASE
HEAP_DICT = {
    IMAGE_BASE - 0xA00F20: None,
} # To emulate the local alloc function
CPUID_EAX_VALUE = 0x000806E9
CPUID_EBX_VALUE = 0x03100800
CPUID_ECX_VALUE = 0x7FFAFBBF
CPUID_EDX_VALUE = 0xBFEBFBFF
IMAGE_BASE = 0xA40000
CODE_BASE_DIFF = 0x1000
LOAD_LIBRARY_OFFSET = 0x80c61 + IMAGE_BASE


def LoadLibWrapper(unpacker, address_to_lib):
    #TODO: add check if the data is in the code (DATA var) or in the stacks.
    offset_to_data = address_to_lib
    #need to find null terminated string
    begin_data = "".join(PROGRAM_DATA[offset_to_data:offset_to_data+0x1000]) #default value TODO: change
    lib_name = begin_data.split('\0')[0]
    result = ctypes.windll.LoadLibrary(lib_name)._handle
    print "[*] Loaded DLL name {0} into {1}".format(lib_name, hex(result))
    return result

def GetProcWrapper(unpacker, addresss_to_enc_string, address_of_handle):
    offset_to_data = addresss_to_enc_string
    begin_data = "".join(PROGRAM_DATA[offset_to_data: offset_to_data + 0x1000])
    enc_string = list(begin_data.split('\0')[0])

    dst_string = ""
    for c in enc_string:
        val = ctypes.c_uint8(ord(c) + 0xc1).value
        val = ctypes.c_uint8(~val).value - 1
        val = ctypes.c_uint8(val - 0x9e).value
        val = ctypes.c_uint8(~val).value - 1
        dst_string += chr(val)
    function = GetProcAddress(address_of_handle, dst_string)
    dst_string = dst_string.split('\x00')[0]
    print "[*] Load function {0} at address {1}".format(dst_string, hex(function))
    
    if dst_string in DLL_IMPORT_FUNCTION: # add to the api call table
        API_CALL_TABLE[function] = DLL_IMPORT_FUNCTION[dst_string]
    #raw_input()
    return function

def GetProcAddress(handle, function_name):
    if function_name == "RtlDosPathNameToNtPathName":
        function_name += "_U"
    return ctypes.windll.kernel32.GetProcAddress(handle, function_name)

def VirtualProtectWp(unpacker, old_prot,new_prot, size, address):
    print "[*] Called to Virtual Protect with argument {0} {1} {2} {3}".format(hex(address), hex(size), hex(new_prot), hex(old_prot))
    set_dword_at_process_data(old_prot, 0x20)
    return 1

def LocalAlloc(unpacker, flags, bytes):
    global HEAP_DICT
    print "[*] Called LocalAlloc size {0} flags {1}".format(hex(bytes), hex(flags))
    for address, data in HEAP_DICT.iteritems():
        if not data: #alloc it
            data = ['\x00'] * 0x100
            HEAP_DICT[address] = data
            print hex(address)
            #raw_input()
            return address

DLL_IMPORT_FUNCTION = {
    "VirtualProtect" :VirtualProtectWp
}

API_CALL_TABLE = {
    0x80C61 + IMAGE_BASE: LoadLibWrapper,
    0x808D1 + IMAGE_BASE: GetProcWrapper,
    0x84038 + IMAGE_BASE: LocalAlloc
}

IMPORT_TABLE = {
    0x84038 + IMAGE_BASE: 0x84038 + IMAGE_BASE
}


def set_word_at_process_data(ea, value):
    PROGRAM_DATA[ea: ea+2] = struct.pack("<H", value)

def set_dword_at_process_data(ea, value):
    PROGRAM_DATA[ea: ea+4] = struct.pack("<I", value)

def set_byte_at_process_data(ea, value):
    PROGRAM_DATA[ea] = struct.pack("<B", value)

def get_byte_from_process_data(ea):
    return PROGRAM_DATA[ea]

def get_word_from_process_data(ea):
    return struct.unpack("<H", "".join(PROGRAM_DATA[ea: ea + 2]))[0]

def get_dword_from_process_data(ea):
    return struct.unpack("<I", "".join(PROGRAM_DATA[ea: ea + 4]))[0]

def read_data(ea):
    return DATA[ea - (IMAGE_BASE + CODE_BASE_DIFF)]

def get_dword_from_address(ea):
    return struct.unpack("<I", DATA[ea - (IMAGE_BASE + CODE_BASE_DIFF): ea + 4 - (IMAGE_BASE + CODE_BASE_DIFF)])[0]

def get_word_from_address(ea):
    return struct.unpack("<H", DATA[ea - (IMAGE_BASE + CODE_BASE_DIFF): ea + 2 - (IMAGE_BASE + CODE_BASE_DIFF)])[0]

def set_byte_at_address(ea, value):
    global DATA
    data = list(DATA)
    data[ea - (IMAGE_BASE + CODE_BASE_DIFF)] = struct.pack("<B",value)
    DATA = "".join(data)


def set_word_to_address(ea, value):
    global DATA
    data = list(DATA)
    data[ea - (IMAGE_BASE + CODE_BASE_DIFF): ea + 2 -(IMAGE_BASE + CODE_BASE_DIFF)] = value
    DATA = "".join(data)

def set_dword_to_address(ea, value):
    global DATA
    data = list(DATA)
    data[ea - (IMAGE_BASE + CODE_BASE_DIFF): ea + 4 -(IMAGE_BASE + CODE_BASE_DIFF)] = value
    DATA = "".join(data)

class Unpacker():
    def __init__(self):
        #This values is derived from the code!
        print "[+] Init"
        self._ip = 0
        self._ip_opcode = 0x7DF4A + IMAGE_BASE # the ip_opcode is hold by the esi, the esi is passing over the opcodes table, it holds by the esi reg.
        self._current_opcode = 0
        self._xor_key = 0x47df4a # the xor key is hold by the ebx, the xor key is hold by the ebx reg
        self._stack = CStack(PROGRAM_DATA, EPB_DEFAULT_VALUE, 52) # the stack of the program, it is looks like, semi-stack. in the Init state of the program we are pushing some variables. it holds by the ebp reg
        self._stacks_dict = {EPB_DEFAULT_VALUE: self._stack}
        self._handlers = {} # the module handles, like kernel32.dl
        # the 3 is the ebx value, it holds the PEB. 
        # the value 2 is the pointer to the stack of seh record.
        self._stack.populate_stack(PROGRAM_DATA, EPB_DEFAULT_VALUE, [0,0,0,0,0, 0, MASK, 0, EPB_DEFAULT_VALUE, 2, ENTRY_POINT_ADDRESS, ENTRY_POINT_ADDRESS, 2,  ENTRY_POINT_ADDRESS, ENTRY_POINT_ADDRESS, 0x286, PEB_DEFAULT_VALUE , 0x5E736B32, 0x820B6FFC])
        self._stack.set_stack_ptr(EPB_DEFAULT_VALUE + 24)
        # for now the stack will be zero out until i found out what we push into the stack.


        self._regs = {} # need to init the regs, it looks like we have 34 regs. 
        for i in range(0,34):
            self._regs["r{0}".format(i)] = 0
        


    # This function will take opcode from the self._ip_opcode, and decode it.
    def decode(self):
        opcode = ord(read_data(self._ip_opcode))
        self._ip_opcode += 1
        opcode ^= self._xor_key & 0xff
        opcode = rol(opcode, 7, 8)
        opcode = ctypes.c_uint8(~opcode).value + 1
        opcode = ror(opcode, 5, 8)
        self._xor_key = ((self._xor_key & 0xff) ^ opcode) + (self._xor_key & 0xffffff00)
        self._current_opcode = opcode
        address_op_code = get_dword_from_address(opcode * 4 + OP_TABLE_ADDRESS)
        address_op_code -= 1
        address_op_code = ctypes.c_uint32(address_op_code + MASK).value
        print "[+] set ip to " + hex(address_op_code) + " and opcode is: " + hex(opcode)
        self._ip = address_op_code

    def run(self):
        if self._current_opcode in OP_DICT:
            OP_DICT[self._current_opcode](self)
        else:
            self._stack.print_stack()
            raise Exception("error, opcode {0} doesnt exists at address {1}".format(hex(self._current_opcode), hex(self._ip)))
        start_address = 0
        for start, stack in self._stacks_dict.iteritems():
            if self._stack == stack:
                start_address = start
        print "----Stack at address {0}----".format(hex(start_address))
        self._stack.print_stack()
        #self.print_reg_debug()
    

    def get_ip(self):
        return self._ip

    def get_xor_key(self):
        return self._xor_key

    def get_ip_opcode(self):
        return self._ip_opcode

    def set_ip(self, value):
        self._ip = value

    def set_xor_key(self, value):
        self._xor_key = value

    def set_ip_opcode(self, value):
        self._ip_opcode = value

    def set_reg_value(self, reg_index, reg_value):
        reg_name = "r{0}".format(reg_index)
        if reg_name in self._regs:
            self._regs[reg_name] = reg_value
        else:
            raise Exception("Unknown Reg")
    
    def get_reg_value(self, reg_index):
        reg_name = "r{0}".format(reg_index)
        if reg_name in self._regs:
            return self._regs[reg_name]
        else:
            raise Exception("Unknown Reg")

    def get_stack_data():
        return self._stack.get_data()

    def get_stack_ptr(self):
        return self._stack.get_stack_ptr()

    def pop_dword_from_stack(self):   
        return self._stack.pop_dword()

    def pop_word_from_stack(self):   
        return self._stack.pop_word()

    def pop_dword_but_inc_word(self):
        return self._stack.pop_dword_but_inc_word()

    def push_dword(self, value):
        self._stack.push_dword(value)
    
    def push_word(self, value):
        self._stack.push_word(value)

    def peek_stack_byte(self, index):
        return self._stack.peek_stack_byte(index)
    
    def peek_stack_word(self, index):
        return self._stack.peek_stack_word(index)

    def peek_stack_dword(self, index):
        return self._stack.peek_stack_dword(index)
    
    def pook_stack_byte(self, index, value):
        self._stack.pook_stack_byte(index, value)

    def pook_stack_word(self, index, value):
        self._stack.pook_stack_word(index, value)

    def pook_stack_dword(self, index, value):
        self._stack.pook_stack_dword(index, value)
    
    def set_stack_ptr(self, index):
        self._stack.set_stack_ptr(index)
    
    def add_stack(self, index, stack):
        self._stacks_dict[index] = stack

    def set_stack(self, stack):
        self._stack = stack

    def get_stack_start_address(self):
        for key, value in self._stacks_dict.iteritems():
            if self._stack == value:
                return key
    
    def put_handler(self, name, address):
        self._handlers[name] = address
    
    def print_reg_debug(self):
        print '~~~REGS~~~'
        reg_values = [0] * 34
        for reg_index, reg_value in self._regs.iteritems():
            reg_values[int(reg_index[1:])] = hex(reg_value)
        for i in range(0, len(reg_values)):
            print "r{0}: {1}".format(i, reg_values[i])
def main():
    global DATA
    with open("BE.exe.bs", 'rb') as f:
        DATA = f.read()[0x1000:] # Read from the start of the text section
    unpacker = Unpacker()
    while True:
        unpacker.decode()
        unpacker.run()

if __name__ == "__main__":
    main()