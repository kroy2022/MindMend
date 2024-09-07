import { HelloWave } from '@/components/HelloWave';
import { View, StyleSheet, Text, TouchableOpacity, Dimensions  } from 'react-native';
import { useNavigation, NavigationProp } from '@react-navigation/native';
import { RootStackParamList } from '../types';
const {width} = Dimensions.get('window');

export default function HomeScreen() {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();

  return (
    <View style={styles.container}>
      <Text style={styles.description}>Your path to safety <HelloWave /></Text>
      <Text style={styles.header}>Stay secure on every journey - try now</Text>
      <TouchableOpacity style={styles.button} onPress={() => 
        navigation.navigate('CreateRoute')
      }>
        <Text style={styles.buttonText}>Find a route!</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  mapcontainer: {
    flex: 1,
  },
  map: {
    width: '100%',
    height: '100%',
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: '#2D3FFF',
  },
  header: {
    marginLeft: 50,
    fontSize: 35,
    fontWeight: "800",
    color: '#FFFFFF',
    width: 200
  },
  description: {
    marginLeft: 50,
    fontSize: 15,
    width: 150,
    lineHeight: 25,
    height: 30,
    justifyContent: "center",
    fontWeight: "300",
    color: '#FFFFFF',
  },
  button: {
    width: width * .50,
    marginTop: 100,
    height: 50,
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    marginLeft: width * .25,
  },
  buttonText: {
    fontWeight: "400",
    fontSize: 18,
  }
});
