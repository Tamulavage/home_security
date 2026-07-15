package com.securityapp

import org.json.JSONObject

object JsonUtils {
    /**
     * Parses a JSON string and returns the value of the specified key.
     *
     * @param json The JSON string to parse.
     * @param key The key to look for.
     * @return The value of the key as a String, or null if the key is not found or parsing fails.
     */
    fun getValueFromJson(json: String, key: String): String? {
        return try {
            val jsonObject = JSONObject(json)
            if (jsonObject.has(key)) {
                jsonObject.getString(key)
            } else {
                null
            }
        } catch (_: Exception) {
            null
        }
    }
}
