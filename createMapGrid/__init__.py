import azure.functions as func
import logging
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import uuid
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    create_grid()

    return func.HttpResponse(
        "This HTTP triggered function executed successfully.",
        status_code=200
        )

# grid configuration
connection_string = "DefaultEndpointsProtocol=https;AccountName=datalaketuhbehhuh;AccountKey=C2te9RgBRHhIH8u3tydAsn9wNd4umdD2axq1ZdcfKh7CZRpL04+D4H6QinE/gckMTUA/dFj1kFpd+ASt4+/8ZA==;EndpointSuffix=core.windows.net"
grid_dict = {
    "name": "Berlin",
    "zoneDef":{
        "gridStartLat": "52.5730",
        "gridStartLong": "13.2770",
        "gridEndLat": "52.39290011580509",
        "gridEndLong": "13.571993619688197"
    },
    "zoneSize": "20",
    "squareSize": "0.5"
}


def create_grid():
    data = grid_dict
    
    zone_def = data.get('zoneDef')
    grid_start_lat = zone_def.get('gridStartLat')
    grid_start_long = zone_def.get('gridStartLong')
    zone_size = float(data.get('zoneSize'))
    square_size = float(data.get('squareSize'))

    grid = pd.DataFrame(columns=['uuid', 'top_left_lat', 'top_left_long', 'bottom_right_lat', 'bottom_right_long'])

    # create a list of all the diagonal points in the grid
    diag_grid_points = []
    for i in np.arange(0, zone_size + square_size, square_size):
        diag_grid_point_ = geodesic(kilometers=i).destination((grid_start_lat, grid_start_long), 90)
        diag_grid_point = geodesic(kilometers=i).destination((diag_grid_point_.latitude, diag_grid_point_.longitude), 180)
        diag_grid_points.append(diag_grid_point)

    # create the grid using the diagonal points
    for i in range(len(diag_grid_points) - 1):
        square_start_lat = diag_grid_points[i].latitude
        square_end_lat = diag_grid_points[i+1].latitude
        print(square_start_lat, square_end_lat)
        for j in range(len(diag_grid_points) - 1):
            square_start_long = diag_grid_points[j].longitude
            square_end_long = diag_grid_points[j+1].longitude
            new_row = {'uuid': uuid.uuid4(), 'top_left_lat': square_start_lat, 'top_left_long': square_start_long, 'bottom_right_lat': square_end_lat, 'bottom_right_long': square_end_long}
            grid.loc[len(grid)] = new_row
    

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container="grid", blob=f"grid.csv")
    print(grid)
    csv_string = grid.to_csv(index=False, encoding='utf-8')
    blob_client.upload_blob(csv_string, blob_type="BlockBlob")
    logging.info(f"uploaded grid.csv to blob storage")