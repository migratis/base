FROM node:20.12.2-alpine
WORKDIR /frontend
COPY package*.json ./
RUN apk add --no-cache python3
RUN rm -rf node_modules
RUN npm cache clear --force
RUN npm i -g npm@10.9.1 
RUN npm i -g cross-env
RUN npm i
RUN npx update-browserslist-db@latest
#CMD ["top"]
COPY . .
RUN chown -R node:node . 
CMD ["npm", "start"]