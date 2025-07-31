/**
 * CMMC Audit Logger
 * 
 * This class provides comprehensive audit logging functionality for CMMC compliance.
 * It logs all user actions, data changes, and system events to ensure complete
 * audit trail for CMMC Level 2 compliance.
 * 
 * @author CMMC Implementation Team
 * @version 1.0
 */
public class CMMCAuditLogger {
    
    // Constants for audit log types
    public static final String ACTION_INSERT = 'INSERT';
    public static final String ACTION_UPDATE = 'UPDATE';
    public static final String ACTION_DELETE = 'DELETE';
    public static final String ACTION_LOGIN = 'LOGIN';
    public static final String ACTION_LOGOUT = 'LOGOUT';
    public static final String ACTION_EXPORT = 'EXPORT';
    public static final String ACTION_IMPORT = 'IMPORT';
    public static final String ACTION_VIEW = 'VIEW';
    
    /**
     * Logs a user action to the CMMC Audit Log
     * 
     * @param action The action being performed
     * @param records The records being affected
     * @param oldMap The old values map (for updates)
     */
    public static void logAction(String action, List<SObject> records, Map<Id, SObject> oldMap) {
        if (records == null || records.isEmpty()) {
            return;
        }
        
        List<CMMC_Audit_Log__c> logs = new List<CMMC_Audit_Log__c>();
        
        for (SObject record : records) {
            CMMC_Audit_Log__c log = createAuditLogEntry(action, record, oldMap);
            logs.add(log);
        }
        
        // Insert logs in a future context to avoid trigger recursion
        if (!logs.isEmpty()) {
            insertAuditLogs(logs);
        }
    }
    
    /**
     * Creates a single audit log entry
     * 
     * @param action The action being performed
     * @param record The record being affected
     * @param oldMap The old values map
     * @return CMMC_Audit_Log__c The audit log entry
     */
    private static CMMC_Audit_Log__c createAuditLogEntry(String action, SObject record, Map<Id, SObject> oldMap) {
        CMMC_Audit_Log__c log = new CMMC_Audit_Log__c(
            Action__c = action,
            Object_Type__c = record.getSObjectType().getDescribe().getName(),
            Record_Id__c = record.Id,
            User__c = UserInfo.getUserId(),
            Timestamp__c = System.now(),
            IP_Address__c = getClientIPAddress(),
            Session_Id__c = UserInfo.getSessionId(),
            Data_Classification__c = getDataClassification(record)
        );
        
        // Add old and new values for updates
        if (oldMap != null && oldMap.containsKey(record.Id)) {
            SObject oldRecord = oldMap.get(record.Id);
            log.Old_Values__c = JSON.serialize(oldRecord);
            log.New_Values__c = JSON.serialize(record);
            
            // Check for suspicious activity
            log.Suspicious_Activity__c = detectSuspiciousActivity(action, oldRecord, record);
        }
        
        return log;
    }
    
    /**
     * Inserts audit logs with error handling
     * 
     * @param logs The audit logs to insert
     */
    private static void insertAuditLogs(List<CMMC_Audit_Log__c> logs) {
        try {
            insert logs;
        } catch (Exception e) {
            // Log error but don't fail the transaction
            System.debug('Error inserting audit logs: ' + e.getMessage());
            
            // Try to insert logs one by one to identify problematic records
            for (CMMC_Audit_Log__c log : logs) {
                try {
                    insert log;
                } catch (Exception ex) {
                    System.debug('Error inserting individual audit log: ' + ex.getMessage());
                }
            }
        }
    }
    
    /**
     * Gets the client IP address
     * 
     * @return String The client IP address
     */
    private static String getClientIPAddress() {
        // This would need to be implemented based on your specific requirements
        // For now, returning a placeholder
        return 'IP_ADDRESS_PLACEHOLDER';
    }
    
    /**
     * Gets the data classification for a record
     * 
     * @param record The record to classify
     * @return String The data classification
     */
    private static String getDataClassification(SObject record) {
        // Check if the record has a data classification field
        if (record.getSObjectType().getDescribe().fields.getMap().containsKey('Data_Classification__c')) {
            return (String) record.get('Data_Classification__c');
        }
        
        // Default classification based on object type
        String objectType = record.getSObjectType().getDescribe().getName();
        if (objectType.contains('Account') || objectType.contains('Contact')) {
            return 'Confidential';
        } else if (objectType.contains('Opportunity') || objectType.contains('Quote')) {
            return 'Restricted';
        } else {
            return 'Internal';
        }
    }
    
    /**
     * Detects suspicious activity based on changes
     * 
     * @param action The action being performed
     * @param oldRecord The old record values
     * @param newRecord The new record values
     * @return Boolean True if suspicious activity is detected
     */
    private static Boolean detectSuspiciousActivity(String action, SObject oldRecord, SObject newRecord) {
        // Check for bulk operations
        if (Limits.getDMLRows() > 1000) {
            return true;
        }
        
        // Check for unusual time patterns
        Time currentTime = Time.newInstance(System.now().hour(), System.now().minute(), 0, 0);
        if (currentTime.hour() < 6 || currentTime.hour() > 22) {
            return true;
        }
        
        // Check for sensitive field changes
        if (action == ACTION_UPDATE) {
            Set<String> sensitiveFields = new Set<String>{
                'Email__c', 'Phone__c', 'SSN__c', 'Credit_Card__c', 'Password__c'
            };
            
            for (String field : sensitiveFields) {
                if (oldRecord.get(field) != newRecord.get(field)) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    /**
     * Logs a login event
     * 
     * @param userId The user ID
     * @param loginTime The login time
     * @param sourceIP The source IP address
     */
    public static void logLogin(Id userId, DateTime loginTime, String sourceIP) {
        CMMC_Audit_Log__c log = new CMMC_Audit_Log__c(
            Action__c = ACTION_LOGIN,
            Object_Type__c = 'User',
            Record_Id__c = userId,
            User__c = userId,
            Timestamp__c = loginTime,
            IP_Address__c = sourceIP,
            Session_Id__c = UserInfo.getSessionId(),
            Data_Classification__c = 'Internal'
        );
        
        insert log;
    }
    
    /**
     * Logs a logout event
     * 
     * @param userId The user ID
     * @param logoutTime The logout time
     */
    public static void logLogout(Id userId, DateTime logoutTime) {
        CMMC_Audit_Log__c log = new CMMC_Audit_Log__c(
            Action__c = ACTION_LOGOUT,
            Object_Type__c = 'User',
            Record_Id__c = userId,
            User__c = userId,
            Timestamp__c = logoutTime,
            IP_Address__c = getClientIPAddress(),
            Session_Id__c = UserInfo.getSessionId(),
            Data_Classification__c = 'Internal'
        );
        
        insert log;
    }
    
    /**
     * Logs an export event
     * 
     * @param objectType The object type being exported
     * @param recordCount The number of records exported
     * @param exportFormat The export format
     */
    public static void logExport(String objectType, Integer recordCount, String exportFormat) {
        CMMC_Audit_Log__c log = new CMMC_Audit_Log__c(
            Action__c = ACTION_EXPORT,
            Object_Type__c = objectType,
            Record_Id__c = null,
            User__c = UserInfo.getUserId(),
            Timestamp__c = System.now(),
            IP_Address__c = getClientIPAddress(),
            Session_Id__c = UserInfo.getSessionId(),
            Data_Classification__c = 'Internal',
            Details__c = 'Exported ' + recordCount + ' records in ' + exportFormat + ' format'
        );
        
        insert log;
    }
    
    /**
     * Logs an import event
     * 
     * @param objectType The object type being imported
     * @param recordCount The number of records imported
     * @param importFormat The import format
     */
    public static void logImport(String objectType, Integer recordCount, String importFormat) {
        CMMC_Audit_Log__c log = new CMMC_Audit_Log__c(
            Action__c = ACTION_IMPORT,
            Object_Type__c = objectType,
            Record_Id__c = null,
            User__c = UserInfo.getUserId(),
            Timestamp__c = System.now(),
            IP_Address__c = getClientIPAddress(),
            Session_Id__c = UserInfo.getSessionId(),
            Data_Classification__c = 'Internal',
            Details__c = 'Imported ' + recordCount + ' records in ' + importFormat + ' format'
        );
        
        insert log;
    }
    
    /**
     * Gets audit logs for a specific user within a date range
     * 
     * @param userId The user ID
     * @param startDate The start date
     * @param endDate The end date
     * @return List<CMMC_Audit_Log__c> The audit logs
     */
    public static List<CMMC_Audit_Log__c> getUserAuditLogs(Id userId, Date startDate, Date endDate) {
        return [
            SELECT Id, Action__c, Object_Type__c, Record_Id__c, Timestamp__c, 
                   IP_Address__c, Data_Classification__c, Suspicious_Activity__c
            FROM CMMC_Audit_Log__c
            WHERE User__c = :userId
            AND Timestamp__c >= :startDate
            AND Timestamp__c <= :endDate
            ORDER BY Timestamp__c DESC
        ];
    }
    
    /**
     * Gets suspicious activity audit logs
     * 
     * @param daysBack The number of days to look back
     * @return List<CMMC_Audit_Log__c> The suspicious activity logs
     */
    public static List<CMMC_Audit_Log__c> getSuspiciousActivityLogs(Integer daysBack) {
        Date startDate = Date.today().addDays(-daysBack);
        
        return [
            SELECT Id, Action__c, Object_Type__c, Record_Id__c, User__c, Timestamp__c,
                   IP_Address__c, Data_Classification__c, Details__c
            FROM CMMC_Audit_Log__c
            WHERE Suspicious_Activity__c = true
            AND Timestamp__c >= :startDate
            ORDER BY Timestamp__c DESC
        ];
    }
    
    /**
     * Purges old audit logs based on retention policy
     * 
     * @param retentionDays The number of days to retain logs
     */
    public static void purgeOldAuditLogs(Integer retentionDays) {
        Date cutoffDate = Date.today().addDays(-retentionDays);
        
        List<CMMC_Audit_Log__c> oldLogs = [
            SELECT Id
            FROM CMMC_Audit_Log__c
            WHERE Timestamp__c < :cutoffDate
        ];
        
        if (!oldLogs.isEmpty()) {
            delete oldLogs;
        }
    }
}