from obsws_python import OBSClient
import time

inicio = time.time()

print("Conectando...")
client = OBSClient(host="localhost", port=4455, password="R6n3NNtb2NbyTFjH")

print("Conectado!")
print("Tempo:", time.time() - inicio)