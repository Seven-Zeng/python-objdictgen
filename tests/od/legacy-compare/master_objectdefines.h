
/* File generated by gen_cfile.py. Should not be modified. */

#ifndef MASTER_OBJECTDEFINES_H
#define MASTER_OBJECTDEFINES_H

/*
    Object defines naming convention:
    General:
        * All characters in object names that does not match [a-zA-Z0-9_] will be replaced by '_'.
        * Case of object dictionary names will be kept as is.
    Index : Node object dictionary name +_+ index name +_+ Idx 
    SubIndex : Node object dictionary name +_+ index name +_+ subIndex name +_+ sIdx 
*/

#define Master_Device_Type_Idx 0x1000
#define Master_Device_Type_Device_Type_sIdx 0x00

#define Master_Error_Register_Idx 0x1001
#define Master_Error_Register_Error_Register_sIdx 0x00

#define Master_Identity_Idx 0x1018
#define Master_Identity_Number_of_Entries_sIdx 0x00
#define Master_Identity_Vendor_ID_sIdx 0x01
#define Master_Identity_Product_Code_sIdx 0x02
#define Master_Identity_Revision_Number_sIdx 0x03
#define Master_Identity_Serial_Number_sIdx 0x04

#endif /* MASTER_OBJECTDEFINES_H */
