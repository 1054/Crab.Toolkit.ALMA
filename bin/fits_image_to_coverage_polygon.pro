PRO fits_image_to_coverage_polygon, SciFitsFile = SciFitsFile, RmsFitsFile = RmsFitsFile
    
    
    ;!PATH = !PATH+":/Users/dzliu/Softwares/IDL/lib"
    ;resolve_all
    ;-- now included in the caller BASH script
    
    IF N_ELEMENTS(SciFitsFile) EQ 0 THEN BEGIN
        PRINT, 'Usage: fits_image_to_coverage_polygon, Sci="sci.fits", Rms="rms.fits"''
        RETURN
    ENDIF
    
    IF N_ELEMENTS(RmsFitsFile) EQ 0 THEN BEGIN
        PRINT, 'Warning! No RMS fits file was given!'
        RmsFitsFile = ''
    ENDIF
    
    ;SciFitsFile = "release_v0_20160313/S2COSMOS-850_20160313_mf_rms.fits"
    ;RmsFitsFile = "release_v0_20160313/S2COSMOS-850_20160313_mf_flux.fits"
    ;OutTextFile = "Coverage_Polygon_S2COSMOS_interpol.txt"
    OutputPolygon = STRMID(SciFitsFile, 0, STRLEN(SciFitsFile)-STRLEN('.fits')) + '.coverage.polygon.txt'
    OutputPolygon_interpol = STRMID(SciFitsFile, 0, STRLEN(SciFitsFile)-STRLEN('.fits')) + '.coverage.polygon.interpol.txt'
    
    ; Read fits image
    IF RmsFitsFile NE '' THEN BEGIN
        FitsImage_RMS = MRDFITS(RmsFitsFile, 0, FitsHeader_RMS)
    ENDIF
    IF SciFitsFile NE '' THEN BEGIN
        FitsImage_SCI = MRDFITS(SciFitsFile, 0, FitsHeader_SCI)
    ENDIF
    NAXIS1 = LONG(sxpar(FitsHeader_SCI, 'NAXIS1'))
    NAXIS2 = LONG(sxpar(FitsHeader_SCI, 'NAXIS2'))
    N1 = NAXIS1
    N2 = NAXIS2
    I1 = NAXIS1-1
    I2 = NAXIS2-1
    
    
    ; Remove high RMS data points
    IF RmsFitsFile NE '' THEN BEGIN
        CooID = WHERE(FitsImage_RMS GT 2.4, /NULL)
        IF N_ELEMENTS(CooID) GT 0 THEN BEGIN
            FitsImage_SCI[CooID] = !VALUES.D_NAN
        ENDIF
    ENDIF
    
    
    ; Check if a pixel has at least one neibourhood as NAN but not all are NAN
    TempImage_LM = FitsImage_SCI & TempImage_LM[*,*] = !VALUES.D_NAN ; left middle
    TempImage_LT = FitsImage_SCI & TempImage_LT[*,*] = !VALUES.D_NAN
    TempImage_MT = FitsImage_SCI & TempImage_MT[*,*] = !VALUES.D_NAN
    TempImage_RT = FitsImage_SCI & TempImage_RT[*,*] = !VALUES.D_NAN
    TempImage_RM = FitsImage_SCI & TempImage_RM[*,*] = !VALUES.D_NAN
    TempImage_RB = FitsImage_SCI & TempImage_RB[*,*] = !VALUES.D_NAN
    TempImage_MB = FitsImage_SCI & TempImage_MB[*,*] = !VALUES.D_NAN
    TempImage_LB = FitsImage_SCI & TempImage_LB[*,*] = !VALUES.D_NAN ; left bottom
    TempImage_LM[1:I1-1,0:I2-1] = FitsImage_SCI[0:I1-2,0:I2-1] ; left middle
    TempImage_LT[1:I1-1,0:I2-2] = FitsImage_SCI[0:I1-2,1:I2-1]
    TempImage_MT[0:I1-1,0:I2-2] = FitsImage_SCI[0:I1-1,1:I2-1]
    TempImage_RT[0:I1-2,0:I2-2] = FitsImage_SCI[1:I1-1,1:I2-1]
    TempImage_RM[0:I1-2,0:I2-1] = FitsImage_SCI[1:I1-1,0:I2-1]
    TempImage_RB[0:I1-2,1:I2-1] = FitsImage_SCI[1:I1-1,0:I2-2]
    TempImage_MB[0:I1-1,1:I2-1] = FitsImage_SCI[0:I1-1,0:I2-2]
    TempImage_LB[1:I1-1,1:I2-1] = FitsImage_SCI[0:I1-2,0:I2-2] ; left bottom
    
    
    ; Check NAN
    CheckArray = ( FINITE(TempImage_LM) + $
                   FINITE(TempImage_LT) + $
                   FINITE(TempImage_MT) + $
                   FINITE(TempImage_RT) + $
                   FINITE(TempImage_RM) + $
                   FINITE(TempImage_RB) + $
                   FINITE(TempImage_MB) + $
                   FINITE(TempImage_LB) )
    
    
    ; Select VALID data points
    IF RmsFitsFile NE '' THEN BEGIN
        CooID = WHERE(FINITE(FitsImage_RMS) AND CheckArray GT 1 AND CheckArray LT 8, /NULL)
    ENDIF ELSE BEGIN
        CooID = WHERE(FINITE(FitsImage_SCI) AND CheckArray GT 1 AND CheckArray LT 8, /NULL)
    ENDELSE
    
    
    ; Obtain xy subscript array
    CatII = INDGEN(N_ELEMENTS(FitsImage_SCI), /LONG)
    CatPI = LONG(CatII MOD NAXIS1)
    CatPJ = LONG(CatII  /  NAXIS1)
    CatPI = CatPI[CooID]
    CatPJ = CatPJ[CooID]
    CenPI = DOUBLE(NAXIS1-1.0)/2.0
    CenPJ = DOUBLE(NAXIS2-1.0)/2.0
    
    
    ; Sort by Tan Angle
    CatDistoc = SQRT((CatPI-CenPI)^2+(CatPJ-CenPJ)^2) ; a distance array to central pixel
    CatTangle = atan((CatPJ-CenPJ), (CatPI-CenPI)) / !PI * 180.0D
    CatSortid = SORT(CatTangle)
    CatPI = CatPI[CatSortid]
    CatPJ = CatPJ[CatSortid]
    CatTangle = CatTangle[CatSortid]
    CatDistoc = CatDistoc[CatSortid]
    
    
    ; Reduce array size
    
    
    ; Print edge
    PerimeterPosAngle = CatTangle
    PerimeterPI = CatPI
    PerimeterPJ = CatPJ
    extast, FitsHeader_SCI, FitsHeaderWCS
    xy2ad, PerimeterPI, PerimeterPJ, FitsHeaderWCS, PerimeterRA, PerimeterDec
    writecol, OutputPolygon, PerimeterRA, PerimeterDec, PerimeterPI, PerimeterPJ, PerimeterPosAngle
    PRINT, 'Ouptut to "'+OutputPolygon+'"'
    
    
    ; Print a better edge
    PerimeterPosAngle = FINDGEN(360)-180.0D ; -180.0 to 180.0
    PerimeterPosAngle[WHERE(PerimeterPosAngle LT MIN(CatTangle), /NULL)] = MIN(CatTangle)
    PerimeterPosAngle[WHERE(PerimeterPosAngle GT MAX(CatTangle), /NULL)] = MAX(CatTangle)
    PerimeterPI = INTERPOL(CatPI, CatTangle, PerimeterPosAngle)
    PerimeterPJ = INTERPOL(CatPJ, CatTangle, PerimeterPosAngle)
    extast, FitsHeader_SCI, FitsHeaderWCS
    xy2ad, PerimeterPI, PerimeterPJ, FitsHeaderWCS, PerimeterRA, PerimeterDec
    writecol, OutputPolygon_interpol, PerimeterRA, PerimeterDec, PerimeterPI, PerimeterPJ, PerimeterPosAngle
    PRINT, 'Ouptut to "'+OutputPolygon_interpol+'"'
    
END


