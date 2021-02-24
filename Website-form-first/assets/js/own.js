print_data = true;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
    }

function printData(){
  // global print_data;
  while(true == true){
    console.log("Hello");
    // await sleep(2000);
  }
}

console.log("hello");
