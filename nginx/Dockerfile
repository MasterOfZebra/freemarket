FROM nginx:alpine

# Copy nginx configuration
COPY freemarket.conf /etc/nginx/conf.d/default.conf

# Copy frontend build
COPY ../frontend/build /usr/share/nginx/html

# Set permissions
RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
