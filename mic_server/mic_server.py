import socket
import time

def main():
    server_ip = "192.168.0.53"
    port = 6050

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((server_ip, port))
    s.listen(1)
    print("Waiting for client connection...")

    c, addr = s.accept()
    print(f"Client connected from {addr}!")

    try:
        while True:
            data = "Connect".encode()
            c.send(data)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        c.close()
        s.close()
        print("Socket closed. Port released.")

if __name__ == "__main__":
    main()
