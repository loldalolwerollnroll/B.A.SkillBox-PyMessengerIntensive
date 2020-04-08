#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport
    all_logged_people: list = None  # Создал список для хранения всех логинов онлайн в текущей сессии
    last_ten_messages: list = None  # Создал список для хранения истории последних 10 сообщений в чате

    def __init__(self, server: 'Server'):
        self.server = server
        self.all_logged_people = []  # При инициализации конструктора создаю экземпляр пустого списка
        self.last_ten_messages = []  # ----------//----------

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                if decoded in self.all_logged_people:  # Проверяю, есть ли логин в списке логинов онлайн
                    self.transport.write("Логин занят! Выберите другой логин\n".encode())  # Если есть, вывожу сообщение
                    self.connection_lost(self)  # Разрываю сооединение
                else:  # Если логина в списке нет, то всё отлично, едем дальше
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.send_history()  # Отправляем пользователю историю последних 10 сообщений через send_history
                    self.all_logged_people.append(self.login)  # Добавляем залогинившийся логин в список логинов онлайн
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        if len(self.last_ten_messages) >= 10:  # Если в списке последних сообщений десять или больше сообщений
            self.last_ten_messages.remove([0])  # Удаляю первое по времени добавления сообщение
            self.last_ten_messages.append(message)  # Добавляю в список новое сообщение
        else:  # А если в списке меньше 10 сообщений
            self.last_ten_messages.append(message)  # То просто добавляю новое сообщение

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):  # Метод, отправляющий историю последних 10 сообщений
        self.transport.write("Вот последние десять сообщений чата:\n".encode())
        for message in self.last_ten_messages:
            self.transport.write(message.encode)



class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
