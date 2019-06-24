import os
from osgeo import ogr, osr


class GridBuilder:
    def __init__(self,
                 prj: osr.SpatialReference,
                 extent: tuple,
                 step_x=1,
                 step_y=1,
                 driver=ogr.GetDriverByName("ESRI Shapefile")):
        self.prj = prj
        self.extent = extent
        self.step_x = step_x
        self.step_y = step_y
        self.driver = driver

    def grid_points(self):
        """
        Calculate coordinates of polygons for GRID.
        x1y1-----x2y2
        |          |
        |          |
        |          |
        x4y4-----x3y3
        """
        x1, y1 = self.extent[0], self.extent[3]
        x2, y2 = self.extent[1], self.extent[2]

        x_start = (x1 // self.step_x) * self.step_x
        y_start = (y1 // self.step_y) * self.step_y + self.step_y
        x_end = (x2 // self.step_x) * self.step_x + self.step_x
        y_end = (y2 // self.step_y) * self.step_y + self.step_y

        print('grid boundary: ', x_start, y_start, x_end, y_end)

        _x, _y = x_start, y_start

        while _x <= x_end and _y >= y_end:
            x1, y1 = _x, _y
            x2, y2 = _x + self.step_x, _y
            x3, y3 = _x + self.step_x, _y - self.step_y
            x4, y4 = _x, _y - self.step_y

            if _x + self.step_x > x_end:
                _x, _y = x_start, _y - self.step_y
            else:
                _x = _x + self.step_x
                yield x1, y1, x2, y2, x3, y3, x4, y4

    @staticmethod
    def polygon(x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Create polygon geometry by coordinates.
        """
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(x1, y1)
        ring.AddPoint(x2, y2)
        ring.AddPoint(x3, y3)
        ring.AddPoint(x4, y4)

        # Create polygon #1
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        return poly

    @staticmethod
    def create_empty_shp(self, path, prj, geometry=ogr.wkbPolygon):
        if os.path.exists(os.path.dirname(path)):
            datasource = self.driver.CreateDataSource(path)
            layer = datasource.CreateLayer('grid_layer', prj, geometry, options=['ENCODING=UTF-8'])
        else:
            raise ValueError("Path doesn't exist")

        # Add the fields we're interested in
        field_name = ogr.FieldDefn("Name", ogr.OFTString)
        field_name.SetWidth(24)
        layer.CreateField(field_name)

        del layer
        del datasource

    def create_grid(self, path):
        self.create_empty_shp(path, self.prj)
        source = self.driver.Open(path, 1)
        layer = source.GetLayer()

        for grid_poly in self.grid_points():
            featureDefn = layer.GetLayerDefn()
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(self.polygon(*grid_poly))
            layer.CreateFeature(feature)
            del feature

        del layer
        del source

    def intersection(self, grid_path, target_path):
        grid_source = self.driver.Open(grid_path, 1)
        grid_layer = grid_source.GetLayer()

        target_source = self.driver.Open(target_path, 1)
        target_layer = target_source.GetLayer()

        for feature1 in grid_layer:
            geom1 = feature1.GetGeometryRef()
            attribute1 = feature1.GetField('Name')
            for feature2 in target_layer:
                geom2 = feature2.GetGeometryRef()
                # select only the intersections
                if geom2.Intersects(geom1):
                    intersection = geom2.Intersection(geom1)
                    dstfeature = ogr.Feature(dstlayer.GetLayerDefn())
                    dstfeature.SetGeometry(intersection)
                    dstfeature.setField(attribute1)
                    dstfeature.setField(attribute2)
                    dstfeature.Destroy()




def test_main():
    driver = ogr.GetDriverByName("ESRI Shapefile")
    source = driver.Open(r"C:\Users\kotov\Documents\github_kot\swd\shp_mesh_builder\data\poly_wgs84.shp")
    layer = source.GetLayer()
    prj = layer.GetSpatialRef()
    extent = layer.GetExtent()

    grid = GridBuilder(prj=prj, extent=extent, step_x=10, step_y=10)

    path = r"C:\Users\kotov\Documents\github_kot\swd\shp_mesh_builder\data\testing\setka.shp"
    grid.create_grid(path)


if __name__=='__main__':
    test_main()