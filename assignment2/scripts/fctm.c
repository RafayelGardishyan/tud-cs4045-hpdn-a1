#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/poll.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <stdbool.h>

#define MODE_CLIENT 1
#define MODE_SERVER 2

#define DEFAULT_SERVER_IP "13.37.3.0"
#define PORT 1337

#define MAX_CONNECTIONS 128
#define SEC_TO_MS 1000
#define RECV_BUFFER_SIZE 4096

#define PACKET_SIZE 1448

#define DEFAULT_QUICKACK 0

void error(const char *msg)
{
        perror(msg);
        exit(1);
}

void show_help()
{
        printf("Usage: fctm [-s DURATION | -c FLOW_SIZE] [-i SERVER_IP]\n\n");
        printf("Arguments:\n");
        printf("-s DURATION: run server that listens for DURATION seconds\n");
        printf("-c FLOW_SIZE: ");
        printf("run client that sends a flow of size FLOW_SIZE (in packets)\n");
        printf("-i SERVER_IP: ");
        printf("the IP address of the server; if omitted, use %s\n",
                        DEFAULT_SERVER_IP);
        printf("-q QUICKACK: ");
        printf("on server, set TCP_QUICKACK option; ");
        printf("use 0 to disable and 1 to enable; ");
        printf("if disabled, the server sends delayed ACKs; ");
        printf("if omitted, use %d\n", DEFAULT_QUICKACK);
        exit(0);
}

void server(int duration, char *server_ip, int quickack)
{
        int sockfd_server, sockfd_client;
        struct sockaddr_in server_addr, client_addr;
        socklen_t len_client;

        struct pollfd fds[MAX_CONNECTIONS];
        int nfds = 1;
        char open_conns[MAX_CONNECTIONS];
        bzero(open_conns, sizeof(open_conns));
        int active;

        char buffer[RECV_BUFFER_SIZE];

        struct timeval server_start, now, server_uptime;

        int err;

        /* Create socket */
        sockfd_server = socket(AF_INET, SOCK_STREAM, 0);
        if (sockfd_server < 0)
                error("Error: could not open socket");

        /* Bind socket to IP address */
        bzero((char *) &server_addr, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_addr.s_addr = inet_addr(server_ip);
        server_addr.sin_port = htons(PORT);

        err = bind(sockfd_server, (struct sockaddr *) &server_addr,
                        sizeof(server_addr));
        if (err < 0)
                error("Error: could not bind socket to IP address");

        /* Start listening for connections */
        listen(sockfd_server, MAX_CONNECTIONS);

        bzero((char *) &fds, sizeof(fds));
        fds[0].fd = sockfd_server;
        fds[0].events = POLLIN | POLLPRI;

        /* Set TCP_QUICKACK */
        err = setsockopt(sockfd_server, IPPROTO_TCP, TCP_QUICKACK,
                 &quickack, sizeof(quickack));
        if (err < 0)
            error("Error: could not set TCP_QUICKACK option");

        /* Start measuring server uptime */
        gettimeofday(&server_start, NULL);

        while (1) {
                err = poll(fds, nfds, duration * SEC_TO_MS);
                if (err < 0)
                        error("Error: could not poll");
                if (err == 0)  /* poll timeout expired */
                        break;

                /* Accept new connections */
                if (fds[0].revents & POLLIN) {
                        sockfd_client = accept(sockfd_server,
                                        (struct sockaddr *) &client_addr,
                                        &len_client);
                        if (sockfd_client < 0)
                                error("Error: could not accept connection");

                        fds[nfds].fd = sockfd_client;
                        fds[nfds].events = POLLIN;
                        open_conns[nfds] = 1;
                        nfds++;
                }

                /* Read from connections */
                for (int i = 1; i < nfds; i++) {
                        if (open_conns[i] == 0)
                                continue;
                        if (fds[i].revents & POLLIN) {
                                bzero(buffer, sizeof(buffer));
                                err = read(fds[i].fd, buffer, sizeof(buffer));
                                if (err < 0)
                                        error("Error: could not read data");
                                if (err == 0) {  /* a sender has finished */
                                        open_conns[i] = 0;
                                        close(fds[i].fd);
                                }
                                /* We must read the data, but we need not do
                                 * anything with it */
                        }
                }

                /* Are we ready to quit the server?
                 * If there are still active connections (i.e., some senders
                 * still try to send data, then don't quit the server */
                active = 0;
                for (int i = 1; i < nfds; i++) {
                        if (open_conns[i] == 1) {
                                active = 1;
                                break;
                        }
                }
                if (active == 1)
                        continue;

                /* Quit when server ran for its intended duration */
                gettimeofday(&now, NULL);
                timersub(&now, &server_start, &server_uptime);
                if ((int) server_uptime.tv_sec >= duration)
                        break;
        }

        close(sockfd_server);
}

void client(uint64_t num_packets, char *server_ip)
{
        uint64_t flow_size_bytes;
        char *flow_contents;

        int sockfd;
        struct sockaddr_in server_addr;
        struct tcp_info info;
        socklen_t len_info;

        struct timeval start, end, fct;

        int err;

        printf("Size: %ld\n", num_packets);

        /* Construct flow contents */
        flow_size_bytes = num_packets * PACKET_SIZE;

        flow_contents = (char *) malloc((size_t) flow_size_bytes);
        for (long i = 0; i < flow_size_bytes - 1; i++)
                flow_contents[i] = 0x41;
        flow_contents[flow_size_bytes - 1] = '\0';

        /* Create socket */
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (sockfd < 0) 
                error("Error: could not open socket");

        /* Connect to the server */
        bzero((char *) &server_addr, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        inet_pton(AF_INET, server_ip, &server_addr.sin_addr);
        server_addr.sin_port = htons(PORT);

        /* FCT measurement start */
        gettimeofday(&start, NULL);

        err = connect(sockfd, (struct sockaddr *) &server_addr,
                        sizeof(server_addr));
        if (err < 0)
                error("Error: could not connect to server");

        /* Send the data (flow contents) */
        err = write(sockfd, flow_contents, strlen(flow_contents));
        if (err < 0) 
                error("Error: could not write message");

        /* Wait for final ACK */
        len_info = sizeof(info);
        do {  /* loop until there are no more unACKed packets */
                getsockopt(sockfd, SOL_TCP, TCP_INFO,
                                (void *) &info, &len_info);
        } while (info.tcpi_unacked > 0);

        /* FCT measurement end */
        gettimeofday(&end, NULL);

        timersub(&end, &start, &fct);
        printf("FCT: %ld.%06lds\n", (long) fct.tv_sec, fct.tv_usec);

        free(flow_contents);

        close(sockfd);
}

int main(int argc, char *argv[])
{
        int opt;
        int mode;
        int server_duration;
        uint64_t num_packets;
        char *server_ip;
        int quickack;

        if (argc < 2 || argc > 7) {
                printf("Illegal number of arguments! Use -h for more info.\n");
                return 1;
        }

        server_ip = DEFAULT_SERVER_IP;
        quickack = DEFAULT_QUICKACK;

        while ((opt = getopt(argc, argv, "hs:c:i:q:")) != -1) {
                switch (opt) {
                case 'h':
                        show_help();
                        break;
                case 's':
                        mode = MODE_SERVER;
                        server_duration = atoi(optarg);
                        break;
                case 'c':
                        mode = MODE_CLIENT;
                        num_packets = (uint64_t) atoi(optarg);
                        break;
                case 'i':
                        server_ip = optarg;
                        break;
                case 'q':
                    quickack = atoi(optarg);
                    break;
                case '?':
                        if (optopt =='c')
                                printf("Please provide a flow size for -c.\n");
                        else
                                printf("Unknown option %c.\n", optopt);
                        return 1;
                default:
                        break;
                }
        }

        if (mode == MODE_SERVER)
                server(server_duration, server_ip, quickack);
        else if (mode == MODE_CLIENT)
                client(num_packets, server_ip);

        return 0;
}

