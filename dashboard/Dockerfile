FROM node:22-alpine

WORKDIR /app/dashboard

COPY dashboard/package.json ./
RUN npm install

COPY dashboard ./

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

