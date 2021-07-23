A multi-level cryptography system based on an idea of using armstrong numbers and matrices for encryption/decryption (the research paper where the idea was originally presented is included in the folder).

The idea behind the system is that the user will provide a key based on which the file will get encrypted. The same key must be used to decrypt the file. During encryption and decryption original file is divided into multiple chunks and process of encryption/decryption is done simultaneously with the use of multithreading.

File Processing:
File processing takes place in two stages. 
There are two classes in the program named FileProcessor and ChunkProcessor.
FileProcessor class takes in the file and divides it into some chunks (8 in our case).
The chunks are then passed on to the ChunkProcessor class along with the key and the function to be performed (encryption/decryption).
New threads get created and activated in the encryption and decryption class's constructors. 
Each chunk gets processed byte by byte and gets stored in a target file, which in the end gets merged in the FileProcessor class.
After merging and getting final encrypted/decrypted file, target files for each chunk created earlier is deleted using os.remove().

Encryption/Decryption in detail:
The user provides a key using which XOR values and base value of 3 matrices is generated.
The matrix is 16 * 16 matrix which has 256 elements and is used to store 1 byte of data.

Consider the base values for 3 matrices to be (28, 212, 242). Further the base values is incremented sequentially and in a cyclic manner to fill up the matrix elements, as follows:

Matrix-1 : 28, 29, 30, ..., 255, 0, 1, 2, 3, ... 27

Matrix-2 : 212, 213, 214, ..., 255, 0, 1, 2, 3, ... 211

Matrix-3 : 242, 243, 244, ..., 255, 0, 1, 2, 3, ... 241

During encryption, Data (byte) to be encrypted is split into 2 nibbles. The higher nibble acts as row and lower one as column. By using these as co-ordinates we get encoded value from matrix.
During decryption, the encoded value which is unique is to be searched in the matrix and co-ordinates (row, col) of matching element are to be treated as the high nibble and lower nibble from which we get original data back.
Moreover instead of creating an actual matrix, we simply use a mathematical formula to get values from the supposed matrix in constant time.
Before the encryption and decryption we also take xor of original data with XOR value that we generated earlier from user key.

