import React from 'react';
import { View, StyleSheet, Text, TouchableOpacity, Dimensions } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import MapView from "react-native-maps";

export default function CreateRoute() {

    const navigation = useNavigation();
    return (
        <View>
            <Text>Hello!!!</Text>
        </View>
    );
}
