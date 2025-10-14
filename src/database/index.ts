import dotenv from 'dotenv'
import mongoose from 'mongoose'

dotenv.config({
  quiet: true
});

async function main() {
  var uri: string = '';

  if (process.env.MONGO_URI == undefined) {
    uri = `mongodb://${process.env.MONGO_DB_USERNAME}:${process.env.MONGO_DB_PASSWORD
      }@${!process.env.MONGO_DB_ADDRESS ? 'database' : process.env.MONGO_DB_ADDRESS
      }:27017/icfj?authSource=admin`;
  }
  else {
    uri = process.env.MONGO_URI;

    if(uri.indexOf("ssl=false") > 0) {
      uri.replace("ssl=false", "ssl=true");
    }
  }

  await mongoose.connect(
    uri,
  );
}

main().catch((err) => console.log(err))
