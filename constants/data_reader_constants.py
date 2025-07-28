from data_fetcher import load_rtm,load_gt,load_sub_geo,load_rtm_main,load_county_geo, county_centroids,load_mt,load_bubbles,load_gt_terr

GT_DF, TERR_GEO = load_gt_terr()
MT_DF = load_mt()
COUNTY_GEO = load_county_geo()
MT_CLUSTER_DF = load_bubbles()
COUNTY_CENTROIDS = county_centroids(COUNTY_GEO)
RTM_DF, COMP_DF = load_rtm_main()
SUBCOUNTY_GEO = load_sub_geo()
gt=load_gt()
rtm=load_rtm()