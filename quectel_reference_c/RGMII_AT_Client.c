#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>


#define SERVER_IP      "192.168.225.1" 
#define SERVER_PORT    1555 
#define BUFFER_SIZE    2048*4

int ql_rgmii_manager_server_fd_state(int n)
{
    if(n == -1 && (errno == EAGAIN || errno == EWOULDBLOCK))
    {
        return 1;
    }
    if( n < 0  && (errno == EINTR || errno == EINPROGRESS))
    {
        return 2;
    }
    else
    {
        return 0;
    }
}

int main(int argc, char **argv)
{
    char buffer_send[BUFFER_SIZE] = {0};
    char buffer_recv[BUFFER_SIZE] = {0};
    char buffer_temp[BUFFER_SIZE] = {0};
    int rv = 0;
    int count = 0;
    int len = 0;
    int i = 0;
    char * datap = NULL;
    
    if(argc == 2)
    {
        if(BUFFER_SIZE-3-2 <= strlen(argv[1])) return 0;
        memcpy(buffer_send+3, argv[1], strlen(argv[1]));
        memcpy(buffer_send+3+strlen(argv[1]), "\r\n", 2);
    }
    else if(argc == 1)
        snprintf(buffer_send+3, BUFFER_SIZE-3, "at\r\n");
    else
        return 0;
    
    
	buffer_send[0] = 0xa4;
    buffer_send[1] = (uint8_t)((strlen(buffer_send+3) & (0xff00))>>8);
    buffer_send[2] = (uint8_t)(strlen(buffer_send+3) & (0x00ff));
    
    
    struct sockaddr_in client_addr;
    memset(&client_addr, 0, sizeof(client_addr));
    client_addr.sin_family = AF_INET;
    client_addr.sin_addr.s_addr = htons(INADDR_ANY);
    client_addr.sin_port = htons(0);
    
    int client_socket = socket(AF_INET,SOCK_STREAM,0);
    if( client_socket < 0)
    {
        printf("Create Socket Failed!\r\n");
        return 0;
    }
    
    if( bind(client_socket,(struct sockaddr*)&client_addr,sizeof(client_addr)))
    {
        printf("Client Bind Port Failed!\r\n"); 
        return 0;
    }
    
    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    if(inet_aton(SERVER_IP, &server_addr.sin_addr) == 0)
    {
        printf("Server IP Address Error!\r\n");
        return 0;
    }
    server_addr.sin_port = htons(SERVER_PORT);
    socklen_t server_addr_length = sizeof(server_addr);
    
    //set_non_blocking_mode client_socket
    fcntl(client_socket, F_SETFL, fcntl(client_socket, F_GETFL, 0) | O_NONBLOCK);
    
    
    printf("RGMII-AT Client Up => %s:%d\r\n", SERVER_IP, SERVER_PORT);
    while(1)
    {
        if(connect(client_socket,(struct sockaddr*)&server_addr, server_addr_length) >= 0)
        {
            break;
        }
        printf("Can Not Connect To => %s:%d\r\n", SERVER_IP, SERVER_PORT);
        sleep(2);
    }
    
    if(1)
    {
        rv = send(client_socket, buffer_send, (3+(int)strlen(buffer_send+3)),0);
        printf("\r\n\r\nsend:\r\n\r\n====================================> send all:%d\r\n==> len=%d head=0x%02x\r\n\"%s\"\r\n", 
                    rv, (int)strlen(buffer_send+3), (uint8_t)buffer_send[0], buffer_send+3);
        if(rv != (3+(int)strlen(buffer_send+3)))
        {
            printf("Send buf not complete\r\n");
            //return 0;
        }
    }
    
    printf("\r\n\r\nrecv:");
    while(1)
    {
        rv = recv(client_socket, buffer_recv, BUFFER_SIZE, 0);
        if(rv >= 3)
        {
            printf("\r\n\r\n====================================> recv all:%d", rv);
            
            datap = buffer_recv;
            do
            {
                len = (((uint16_t)((uint8_t)*(datap+1))<<8) | ((uint16_t)((uint8_t)*(datap+2)) & (0x00ff)));
                memset(buffer_temp, 0, sizeof(buffer_temp));
                memcpy(buffer_temp, datap+3, len);
                
                printf("\r\n==> len=%d head=0x%02x\r\n\"%s\"\r\n", len, (uint8_t)*(datap), buffer_temp);
                for(i=0; i<len; i++)
                {
                    //printf("0x%02x ", buffer_temp[i]);
                }
                printf("\r\n");
                
                rv = rv-len-3;
                if(rv>0)
                    datap = buffer_recv+3+len;
                if(rv<0)
                    printf("client_socket recv not complete\r\n");
                
            }while(rv > 0);
            
            memset(buffer_recv, 0, sizeof(buffer_recv));
            
        }
        else if(rv > 0)
        {
            printf("client_socket recv error internal\r\n");
            break;
        }
        else
        {
            if(!ql_rgmii_manager_server_fd_state(rv))
            {
                printf("client_socket recv error\r\n");
                break;
            }
            
        }
        
        count++;
        usleep(10*1000);
        
        if(count == 300)
        {
            break;
        }
        
    }
    printf("\r\n");
    close(client_socket);
    return 0;
}