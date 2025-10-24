FROM nginx:alpine

# Expose port 80 (default nginx port)
EXPOSE 80

# Copy static assets
COPY index.html /usr/share/nginx/html/index.html
COPY welcome.html /usr/share/nginx/html/welcome.html

# Copy nginx configuration template and entrypoint
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

CMD ["/docker-entrypoint.sh"]
