import socket
import ssl
from html.parser import HTMLParser

# https://stackoverflow.com/questions/46266401/pars-and-extract-urls-inside-an-html-web-content-without-using-beautifulsoup-or
# https://docs.python.org/3/library/html.parser.html
fakebook_pages = []

class FakebookHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':  # only lookings at the links tags
            for attrs in attrs:  # attrs will be the href and the link in a tuple
                link = attrs[1]  # the fakebook link or accounts/logout link
                if link.startswith("/fakebook"):  # only want to fakebook pages link
                    fakebook_pages.append(link)


def get(path, ss, host, cookie1=None, cookie2=None):
    if cookie1 is None and cookie2 is None:  # no cookies given
        msg = f'GET {path} HTTP/1.1\r\n' \
              f'{host}\r\n\r\n'
    elif cookie2 is None:  # only cookie 1 given
        msg = f'GET {path} HTTP/1.1\r\n' \
              f'{host}\r\n' \
              f'Cookie: {cookie1}\r\n\r\n'
    else:  # both cookies given
        msg = f'GET {path} HTTP/1.1\r\n' \
              f'{host}\r\n' \
              f'Cookie: {cookie1}; {cookie2}\r\n\r\n'

    ss.send(msg.encode())


def receive(ss):
    msg = ss.recv(4096).decode()
    print(msg)
    return msg


def login(ss, path, Host, body_len, body, cookie1, cookie2):
    post_msg = f'POST {path} HTTP/1.1\r\n' \
               f'{Host}\r\n' \
               'Content-Type: application/x-www-form-urlencoded\r\n' \
               f'Content-Length: {body_len}\r\n' \
               f'Cookie: {cookie2}; {cookie1}\r\n\r\n' \
               f'{body}'
    print(post_msg)
    ss.send(post_msg.encode())


def cookie_jar(msg):
    msg = msg.split()

    # find index and store first cookie
    first_index = msg.index("Set-Cookie:")
    first_cookie = msg[first_index + 1].strip(";")

    try:  # try finding second cookie, if there is only one, then an error will occur
        msg = msg[first_index + 1:]
        second_index = msg.index("Set-Cookie:")
        second_cookie = msg[second_index + 1].strip(";")
    except:  # error, meaning only 1 cookie exists
        return first_cookie

    return first_cookie, second_cookie


def middletoken(msg):
    msg = msg.split()
    index = msg.index('name="csrfmiddlewaretoken"')
    token = msg[index + 1]
    token = token.split("=")
    token = token[1].replace('"', '')
    token = token.replace(">", "")

    return token


def create_loginbody(user, passw, token):
    return f'username={user}&' \
           f'password={passw}&' \
           f'csrfmiddlewaretoken={token}&' \
           'next=/fakebook'


def main():
    Host = "Host: project2.5700.network"
    root_path = "/"
    login_path = "/accounts/login/?next=/fakebook/"
    home_fakebook = "/fakebook/"
    users = ['maynard.ma', 'dhaundiyal.s']
    passwords = ['002958850', '0']

    # http is based on TCP so create a TCP/IP socket
    # building connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss = ssl.wrap_socket(s)
    addr = ('project2.5700.network', 443)  # port 443 (default https protocol) for data transmission on encrypt. network
    ss.connect(addr)

    print("**************************Starting session**************************")

    # get the root page
    get(root_path, ss, Host)

    # check the received message
    msg = receive(ss)

    # store the session cookie
    cookie_1 = cookie_jar(msg)

    print("**************************Server responding**************************")

    # send get request for login page
    get(login_path, ss, Host, cookie1=cookie_1)

    # check the received message
    msg = receive(ss)

    # retrieving csrf cookie and middletoken
    cookie2 = cookie_jar(msg)
    token = middletoken(msg)

    print("**************************Logging in**************************")
    body = create_loginbody(users[0], passwords[0], token)
    body_len = len(body.encode())

    # login user
    login(ss, login_path, Host, body_len, body, cookie_1, cookie2)

    msg = receive(ss)

    # store new cookies
    cookie3, cookie4 = cookie_jar(msg)

    print("**************************Getting my fakebook page**************************")

    # send request to go to my fakebook page
    get(home_fakebook, ss, Host, cookie1=cookie3, cookie2=cookie4)

    # receive response message in a loop
    msg = receive(ss)

    parser = FakebookHTMLParser()
    print("*************")
    parser.feed(msg)
    print(fakebook_pages)
    print("*************")


    """
        Here is where the looping and queue stuff will need to start to keep tracking of pages visted/to be visited
    """

    print("**************************Getting friends fakebook pages examples**************************")
    # checking that we can successfully go to other people's pages

    for each in fakebook_pages:
        get(each, ss, Host, cookie1=cookie3, cookie2=cookie4)
        msg = receive(ss)


# ss.close()


main()
