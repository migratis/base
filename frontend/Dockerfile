# Base frontend — CRA dev server on modern Node.
# node:20.12.2-alpine → Node 26, matching the NODE_VERSION this app is pinned
# to. The install below runs at BUILD time on purpose: compose mounts an
# anonymous volume over /frontend/node_modules, and that volume is seeded from
# the image the first time the container is created. So a dependency added to
# package.json reaches a running container only after `--build` AND a recreate
# that renews the volume — react-leaflet sat declared-but-absent for exactly
# that reason.
FROM node:26.8.1-alpine
WORKDIR /frontend
COPY package*.json ./
RUN apk add --no-cache python3
RUN rm -rf node_modules
RUN npm cache clear --force
RUN npm i -g npm
RUN npm i -g cross-env
# package-lock.json is stale vs package.json (upstream of this edit) — npm ci
# refuses with EUSAGE, so resolve like the previous image did with npm install.
RUN npm install --no-audit --no-fund
RUN npx update-browserslist-db@latest
#CMD ["top"]
COPY . .
RUN chown -R node:node .
CMD ["npm", "start"]
