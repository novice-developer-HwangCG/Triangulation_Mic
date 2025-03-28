import socket
import time

def main():
    server_ip = "192.168.0.53"
    port = 6050

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((server_ip, port))
            print("Connected to server!")

            while True:
                data = s.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode()}")
        except (socket.timeout, ConnectionRefusedError):
            print("server check (Cant Connected to Server)")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            s.close()

        print("Reconnecting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main()
