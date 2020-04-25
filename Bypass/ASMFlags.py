
SIZE_OF_FLAGS = 16
CARRY_FLAG_INDEX = 0
PARITY_FLAG_INDEX = 2
ADJUST_FLAG_INDEX = 4
ZERO_FLAG_INDEX = 6
SIGN_FLAG_INDEX = 7
OVER_FLOW_FLAG_INDEX = 11
#all the others dont matter
class ASMFlags:
    def __init__(self):
        self._flags = ['0'] * SIZE_OF_FLAGS
        self._flags[1] = '1' # Reserved
        self._flags[9] = '1' # set hardware interupt
    def set_carry(self):
        self._flags[CARRY_FLAG_INDEX] = '1'
    
    def unset_carry(self):
        self._flags[CARRY_FLAG_INDEX] = '0'

    def set_parity(self):
        self._flags[PARITY_FLAG_INDEX] = '1'

    def unset_parity(self):
        self._flags[PARITY_FLAG_INDEX] = '0'
    
    def set_adjust(self):
        self._flags[ADJUST_FLAG_INDEX] = '1'

    def unset_adjust(self):
        self._flags[ADJUST_FLAG_INDEX] = '0'
    
    def set_zero(self):
        self._flags[ZERO_FLAG_INDEX] = '1'

    def unset_zero(self):
        self._flags[ZERO_FLAG_INDEX] = '0'

    def set_sign(self):
        self._flags[SIGN_FLAG_INDEX] = '1'

    def unset_sign(self):
        self._flags[SIGN_FLAG_INDEX] = '0'
    
    def set_overflow(self):
        self._flags[OVER_FLOW_FLAG_INDEX] = '1'

    def unset_overflow(self):
        self._flags[OVER_FLOW_FLAG_INDEX] = '0'
    
    def get_binary(self):
        return int("".join(self._flags[::-1]),2)
    
