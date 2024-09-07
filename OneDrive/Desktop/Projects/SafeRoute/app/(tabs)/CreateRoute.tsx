import React from 'react';
import { View, StyleSheet, Text, TouchableOpacity, Dimensions, Button } from 'react-native';
import { useNavigation, NavigationProp } from '@react-navigation/native';
import MapView from "react-native-maps";
import { RootStackParamList } from '../types';

export default function CreateRoute() {
    const navigation = useNavigation<NavigationProp<RootStackParamList>>();
    
    return (
        <View style={styles.container}>
            <MapView style={styles.map} />
            <TouchableOpacity onPress={() =>
                navigation.navigate("Home")
            }>
                <Text>Return</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    map: {
        height: '80%',
        width: '100%'
    }
})