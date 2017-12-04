<?php

/*

$data = '{
        "sensor":[
        "AAAF4AAAAAAAAD1QAAAAAAAAWcUAAEhZ",
        "AAAFwAAAADAAAD2AAAAAAAAAWZQAAEe2",
        "AAAFsAAAAEAAAD1gAAAAAAAAWXgAAEfZ",
        "AAAFsAAAAHAAAD1wAAAAAAAAWa8AAEfo",
        "AAAF0AAAACAAAD0wAAAAAAAAWaUAAEf3",
        "AAAFsP///9AAAD1AAAAAAAAAWZYAAEgA",
        "AAAFsAAAADAAAD0AAAAAAAAAWaIAAEfG",
        "AAAFsP/// AAAD0QAAAAAAAAWY0AAEfu",
        "AAAFsAAAAAAAAD0wAAAAAAAAWaoAAEf2",
        "AAAFwP///9AAAD1QAAAAAAAAWZoAAEfh"
        ]
        }';
*/

$data = '{"sensor":'.$_POST['data'];
$dataDecode = json_decode($data,true);

if(file_exists ( "sensor.csv" ))
    $file = fopen("sensor.csv","a");
else
    $file = fopen("sensor.csv","w");


foreach ($dataDecode["sensor"] as $list){
        fputcsv($file,Array($list));
}


fclose($file);

echo "write CSV file complete.";
?>