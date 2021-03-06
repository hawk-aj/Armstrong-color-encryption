'''a cascaded encrypter and decrypter based the reasearch paper included in the folder'''
'''encryption of audio/video/text/image files is being performed using Armstrong numbers
, unique used key and a user based color
multithreading was also used to improve execution time'''

import os
import threading
import abc

import time

class KeyGenerator:
    ARMSTRONG_DIGITS = (1, 5, 3, 7, 0, 3, 7, 1, 4, 0, 7)
    KEY_LENGTH = len(ARMSTRONG_DIGITS)

    def __init__(self, user_remark):
        self.numerickey = []
        sum = 0

        for k in user_remark:
            temp = ord(k)
            if (temp not in self.numerickey) and (len(self.numerickey) < KeyGenerator.KEY_LENGTH):
                self.numerickey.append(temp)
                sum += temp

        if(len(self.numerickey) < KeyGenerator.KEY_LENGTH):
            raise Exception('Weak Key')

        self.numerickey = self.numerickey[:KeyGenerator.KEY_LENGTH]
        for x in range(KeyGenerator.KEY_LENGTH):
            self.numerickey[x] = (self.numerickey[x] + KeyGenerator.ARMSTRONG_DIGITS[x])%256

        self.numerickey.append(sum)

    def get_key(self):
        return self.numerickey

class ByteManager:
    @classmethod
    def byte_to_nibbles(cls, byte):
        lower_nibble = byte & 0xF
        higher_nibble = byte >> 4
        return (higher_nibble, lower_nibble)

    @classmethod
    def nibble_to_bytes(cls, nibbles):
        return (nibbles[0] << 4) | nibbles[1]

class Cryptography(abc.ABC):
    def __init__(self, user_remark):
        self.numericKey = KeyGenerator(user_remark).get_key()
        self.color_index = 0
        self.numerickey_index = 0
        self.color = self.makeColor()
        self.size = len(self.color)

    def makeColor(self):
        r = (sum(self.numericKey[:4]) + self.numericKey[-1]) % 256
        g = (sum(self.numericKey[4:8]) + self.numericKey[-1]) % 256
        b = (sum(self.numericKey[8:12]) + self.numericKey[-1]) % 256
        #print(r,g,b)
        return r,g,b

    @abc.abstractmethod
    def process(self, data):
        pass

class Encrypter(Cryptography):
    def __init__(self,user_remark):
        Cryptography.__init__(self,user_remark)
        self.ii = 0
    def process(self,data):
        #level1
        data = data ^ self.numericKey[self.numerickey_index]
        self.numerickey_index = (self.numerickey_index + 1) % KeyGenerator.KEY_LENGTH

        if(self.ii<15):
            #print(self.numerickey_index,"ni numeric key",self.numericKey)
            self.ii+=1
        #level2
        row , col = ByteManager.byte_to_nibbles(data)

        encoded = (self.color[self.color_index] + row * 16 + col) % 256
        self.color_index = (self.color_index + 1) % self.size

        return encoded

class Decrypter(Cryptography):
    def __init__(self, user_remark):
        Cryptography.__init__(self, user_remark)
        self.i=0

    def process(self, encoded):
        #level2
        temp = (encoded - self.color[self.color_index] + 256) % 256
        row = temp // 16
        col = temp % 16
        self.color_index = (self.color_index + 1) % self.size
        data = ByteManager.nibble_to_bytes((row, col))

        #level1
        data = data ^ self.numericKey[self.numerickey_index]
        self.numerickey_index = (self.numerickey_index +1) % KeyGenerator.KEY_LENGTH

        if(self.i==0):
            self.i+=1
        return data


class ChunkProcessor:
    def __init__(self, src_file_name, trgt_file_name, start_pos, end_pos, objCrypto):
        #input data
        self.src_filename = src_file_name
        self.trgt_filename = trgt_file_name
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.objCrypto = objCrypto

        #a thread member of the class
        self.thrd = threading.Thread(target = self.process)
        #print(threading.active_count())
        #print(threading.enumerate())
        #activate the thread
        self.thrd.start()

    def process(self):
        #open the source file for reading
        src_handle = open(self.src_filename, 'rb')
        trgt_handle = open(self.trgt_filename, 'wb')

        #print(self.objCrypto.numericKey)
        #ensure that chunk is read within the limits
        src_handle.seek(self.start_pos, 0)
        x = self.start_pos
        while x < self.end_pos:
                buff = int.from_bytes(src_handle.read(1), byteorder='big')
                buff = self.objCrypto.process(buff)
                trgt_handle.write(int.to_bytes(buff, length=1, byteorder='big'))
                x+=1

        trgt_handle.close()
        src_handle.close()

class FileProcessor:
    def __init__(self, src_file_name, trgt_file_name, action, user_key):
        if not os.path.exists(src_file_name):  #checking weather the file exists or not
            raise Exception(src_file_name + 'does not exist..')
        self.src_file_name = src_file_name
        self.trgt_file_name = trgt_file_name
        self.action = action
        self.user_key = user_key

    def process(self):
        n = 8 # number of parts the file will be divided into

        chunks = self.divide_into_chunks(n)  
        cps = []

        for ch in chunks:
            if self.action == 'E':
                objE = Encrypter(self.user_key)
                cps.append(ChunkProcessor(self.src_file_name, ch[0], ch[1], ch[2], objE))
            elif self.action =='D':
                objD = Decrypter(self.user_key)
                cps.append(ChunkProcessor(self.src_file_name, ch[0], ch[1], ch[2], objD))

        #suspend this thread until chunk processors are done
        for cp in cps:
            #print(threading.active_count())
            #print(threading.enumerate())
            cp.thrd.join()

        #merge into the trgt_file_name
        trgt_handle = open(self.trgt_file_name, 'wb')
        for ch in chunks:
            ch_handle = open(ch[0], 'rb')
            while True:
                buff = ch_handle.read(2048)
                if not buff:
                    break
                trgt_handle.write(buff)
            ch_handle.close()

        trgt_handle.close()

        #delete the chunk files
        for ch in chunks:
            os.remove(ch[0])         

    def divide_into_chunks(self, n):
        chunks = []

        #chunk boundries
        src_file_size = os.path.getsize(self.src_file_name)
        size_of_chunk = src_file_size // n
        end = 0

        #generate the names
        tup = os.path.splitext(self.src_file_name)

        i = -1
        for i in range(n-1) :
            start = end
            end = start + size_of_chunk
            chunks.append( ( tup[0] + str(i) + tup[1], start, end ) )

        #nth chunk
        chunks.append( ( tup[0]+str(i+1)+tup[1], end, src_file_size ) )
        return chunks


def main():
    src_file = "C:/Users/aj240/Downloads/amethyst_21_stuff/Final_ComicStan.png"
    encrypted_file ="Data/test-en.png"
    final_file = 'Data/test-de.png'

    user_key = 'zqpenteryourkeyheretostartprocess'

    start_time = time.time()

    size_e = os.path.getsize(src_file)
    print("size of the encrypted file ",size_e," in bytes")

    fp1 = FileProcessor(src_file, encrypted_file, 'E', user_key)            #encryption
    fp1.process()

    fp2 = FileProcessor(encrypted_file, final_file, 'D', user_key)          #decryption
    fp2.process()

    size_ff = os.path.getsize(final_file)
    print("size of the final file ", size_ff, "in bytes")

    end_time = time.time()
    print("time taken to run the code in seconds : ", end_time-start_time)

    print('File Decrypted Successfully')

main()
         
